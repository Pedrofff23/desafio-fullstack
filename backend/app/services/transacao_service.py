"""Service de movimentações de estoque.

Regras:
- Entrada: cria/usa um lote e registra a entrada (histórico de fornecedor e custo).
- Saída: vincula a uma entrada com saldo disponível. A integridade (não deixar
  saldo negativo sob concorrência) é garantida pelo trigger `validar_saldo_saida`.
- Transações são imutáveis (auditoria): não há exclusão/edição.
- Histórico unificado (entradas + saídas) com filtros.
"""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.localidade import Contato, Endereco
from app.models.transacao import (
    Fornecedor,
    RegistroEntrada,
    RegistroSaida,
)
from app.repositories.localidade_repository import LocalidadeRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.transacao_repository import TransacaoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.transacao import (
    EstoqueEntradaOut,
    FornecedorCreate,
    FornecedorOut,
    MovimentoOut,
    RegistroEntradaCreate,
    RegistroEntradaOut,
    RegistroSaidaCreate,
    RegistroSaidaOut,
)


class TransacaoService:
    """Regras de negócio de estoque (entrada/saída/histórico)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TransacaoRepository(session)
        self.localidade_repo = LocalidadeRepository(session)
        self.produto_repo = ProdutoRepository(session)

    # ------------------------------------------------------------------
    # Fornecedores
    # ------------------------------------------------------------------
    async def criar_fornecedor(self, data: FornecedorCreate) -> FornecedorOut:
        if not await self.localidade_repo.cidade_pertence_ao_estado(
            data.endereco.cidade_id, data.endereco.estado_id
        ):
            raise HTTPException(
                status_code=400,
                detail="A cidade informada não pertence ao estado selecionado",
            )
        endereco = Endereco(**data.endereco.model_dump(exclude={"estado_id"}))
        contato = Contato(**data.contato.model_dump())
        fornecedor = Fornecedor(
            nome_empresa=data.nome_empresa,
            contato=contato,
            endereco=endereco,
            ativo=data.ativo,
        )
        try:
            fornecedor = await self.repo.add_fornecedor(fornecedor)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Fornecedor, contato ou endereço já cadastrado",
            ) from exc
        fornecedor = await self.repo.get_fornecedor(fornecedor.id)
        return FornecedorOut.model_validate(fornecedor, from_attributes=True)

    async def listar_fornecedores(self) -> list[FornecedorOut]:
        fornecedores = await self.repo.list_fornecedores()
        return [
            FornecedorOut.model_validate(f, from_attributes=True) for f in fornecedores
        ]

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------
    async def registrar_entrada(
        self, data: RegistroEntradaCreate, funcionario_id: int
    ) -> RegistroEntradaOut:
        lote = await self.produto_repo.get_lote(data.lote_id)
        if lote is None or lote.excluido_em is not None or not lote.ativo:
            raise HTTPException(status_code=404, detail="Lote não encontrado")

        produto = await self.produto_repo.get(lote.produto_id)
        if produto is None or produto.excluido_em is not None or not produto.ativo:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        fornecedor = await self.repo.get_fornecedor(data.fornecedor_id)
        if fornecedor is None or not fornecedor.ativo:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

        localizacao_id = data.localizacao_id
        if localizacao_id is None:
            # Usa a localização preferencial do produto (trigger também garante).
            localizacao_id = produto.localizacao_id
            if localizacao_id is None:
                raise HTTPException(
                    status_code=400, detail="Produto sem localização cadastrada"
                )
        elif await self.produto_repo.get_localizacao(localizacao_id) is None:
            raise HTTPException(status_code=400, detail="Localização não encontrada")

        entrada = RegistroEntrada(
            **data.model_dump(
                exclude={"localizacao_id"},
                exclude_none=True,
            ),
            localizacao_id=localizacao_id,
            # Campo legado obrigatório no banco base. Não faz parte do contrato
            # público e apenas preserva o preço vigente no momento da entrada.
            preco_sugerido=produto.preco,
            funcionario_id=funcionario_id,
        )
        entrada = await self.repo.add_entrada(entrada)
        await self.session.commit()
        return RegistroEntradaOut.model_validate(entrada, from_attributes=True)

    # ------------------------------------------------------------------
    # Saída (valida slado; integridade sob concorrência via trigger)
    # ------------------------------------------------------------------
    async def registrar_saida(
        self, data: RegistroSaidaCreate, funcionario_id: int
    ) -> RegistroSaidaOut:
        entrada = await self.repo.get_entrada(data.entrada_id)
        if entrada is None:
            raise HTTPException(status_code=404, detail="Entrada não encontrada")

        saldo = await self.repo.saldo_entrada(data.entrada_id)
        if data.quantidade > saldo:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente. Disponível: {saldo}",
            )

        saida = RegistroSaida(
            **data.model_dump(exclude_none=True),
            funcionario_id=funcionario_id,
        )
        try:
            saida = await self.repo.add_saida(saida)
            await self.session.commit()
        except DBAPIError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=400,
                detail="Saldo insuficiente para concluir a saída",
            ) from exc
        return RegistroSaidaOut.model_validate(saida, from_attributes=True)

    # ------------------------------------------------------------------
    # Estoque atual
    # ------------------------------------------------------------------
    async def entradas_disponiveis(
        self, produto_id: int | None = None
    ) -> list[EstoqueEntradaOut]:
        linhas = await self.repo.entradas_disponiveis(produto_id=produto_id)
        return [EstoqueEntradaOut.model_validate(linha) for linha in linhas]

    async def estoque_atual(
        self, page: int = 1, size: int = 20
    ) -> PaginatedResponse[dict]:
        linhas, total = await self.repo.estoque_atual_por_produto(page=page, size=size)
        return PaginatedResponse.build(linhas, total, page, size)

    # ------------------------------------------------------------------
    # Histórico
    # ------------------------------------------------------------------
    async def historico(
        self,
        page: int = 1,
        size: int = 20,
        produto_id: int | None = None,
        tipo: str | None = None,
        funcionario_id: int | None = None,
        quantidade: float | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> PaginatedResponse[MovimentoOut]:
        linhas, total = await self.repo.historico(
            page=page,
            size=size,
            produto_id=produto_id,
            tipo=tipo,
            funcionario_id=funcionario_id,
            quantidade=quantidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        out: list[MovimentoOut] = [
            MovimentoOut(
                id=r["id"],
                tipo=r["tipo"],
                tipo_movimento=r["tipo_movimento"],
                produto_id=r.get("produto_id"),
                produto_nome=r.get("produto_nome"),
                lote_id=r.get("lote_id"),
                quantidade=float(r["quantidade"]),
                data_movimento=r["data_movimento"],
                preco=float(r["preco"]) if r.get("preco") is not None else None,
                observacao=r.get("observacao"),
                funcionario_id=r.get("funcionario_id"),
                responsavel_email=r.get("responsavel_email"),
            )
            for r in linhas
        ]
        return PaginatedResponse.build(out, total, page, size)
