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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.produto import Produto
from app.models.transacao import (
    Fornecedor,
    RegistroEntrada,
    RegistroSaida,
)
from app.models.usuario import Funcionario, Usuario
from app.repositories.transacao_repository import TransacaoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.transacao import (
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

    # ------------------------------------------------------------------
    # Fornecedores
    # ------------------------------------------------------------------
    async def criar_fornecedor(self, data: FornecedorCreate) -> FornecedorOut:
        # Criar contato e endereço necessários (FKs NOT NULL)
        from app.models.localidade import Contato, Endereco, Cidade

        cidade = await self.session.execute(
            select(Cidade).order_by(Cidade.id).limit(1)
        )
        cidade = cidade.scalar_one_or_none()
        if cidade is None:
            raise HTTPException(status_code=400, detail="Cidades não cadastradas no banco")

        endereco = Endereco(
            logradouro="Endereço do fornecedor",
            numero="0",
            complemento=None,
            cep="00000000",
            bairro="Centro",
            cidade_id=cidade.id,
        )
        contato = Contato(codigo_pais="+55", ddd="00", numero="000000000")
        self.session.add(endereco)
        self.session.add(contato)
        await self.session.flush()

        fornecedor = Fornecedor(
            nome_empresa=data.nome_empresa,
            contato_id=contato.id,
            endereco_id=endereco.id,
            ativo=data.ativo,
        )
        fornecedor = await self.repo.add_fornecedor(fornecedor)
        await self.session.commit()
        return FornecedorOut.model_validate(fornecedor, from_attributes=True)

    async def listar_fornecedores(self) -> list[FornecedorOut]:
        fornecedores = await self.repo.list_fornecedores()
        return [
            FornecedorOut.model_validate(f, from_attributes=True)
            for f in fornecedores
        ]

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------
    async def registrar_entrada(
        self, data: RegistroEntradaCreate, funcionario_id: int
    ) -> RegistroEntradaOut:
        from app.models.produto import Lote

        lote = await self.session.get(Lote, data.lote_id)
        if lote is None:
            raise HTTPException(status_code=404, detail="Lote não encontrado")

        fornecedor = await self.repo.get_fornecedor(data.fornecedor_id)
        if fornecedor is None:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

        localizacao_id = data.localizacao_id
        if localizacao_id is None:
            # Usa a localização preferencial do produto (trigger também garante).
            from app.models.produto import Produto

            produto = await self.session.get(Produto, lote.produto_id)
            localizacao_id = produto.localizacao_id if produto else None
            if localizacao_id is None:
                raise HTTPException(
                    status_code=400, detail="Produto sem localização cadastrada"
                )

        entrada = RegistroEntrada(
            lote_id=data.lote_id,
            fornecedor_id=data.fornecedor_id,
            localizacao_id=localizacao_id,
            quantidade=data.quantidade,
            preco_custo=data.preco_custo,
            preco_sugerido=data.preco_sugerido,
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
            entrada_id=data.entrada_id,
            quantidade=data.quantidade,
            preco_venda=data.preco_venda,
            funcionario_id=funcionario_id,
        )
        saida = await self.repo.add_saida(saida)
        await self.session.commit()
        return RegistroSaidaOut.model_validate(saida, from_attributes=True)

    # ------------------------------------------------------------------
    # Estoque atual
    # ------------------------------------------------------------------
    async def estoque_atual(self, page: int = 1, size: int = 20) -> PaginatedResponse[dict]:
        linhas = await self.repo.estoque_atual_por_produto()
        total = len(linhas)
        inicio = (page - 1) * size
        fatia = linhas[inicio : inicio + size]
        return PaginatedResponse.build(fatia, total, page, size)

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
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> PaginatedResponse[MovimentoOut]:
        linhas, total = await self.repo.historico(
            page=page,
            size=size,
            produto_id=produto_id,
            tipo=tipo,
            funcionario_id=funcionario_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Carrega nomes de produtos e e-mails em lote (evita N+1 queries)
        produto_ids = {r["produto_id"] for r in linhas if r.get("produto_id")}
        func_ids = {r["funcionario_id"] for r in linhas if r.get("funcionario_id")}

        nomes_produto: dict[int, str] = {}
        if produto_ids:
            rows = await self.session.execute(
                select(Produto.id, Produto.nome).where(Produto.id.in_(produto_ids))
            )
            nomes_produto = {row[0]: row[1] for row in rows}

        emails_func: dict[int, str] = {}
        if func_ids:
            rows = await self.session.execute(
                select(Usuario.funcionario_id, Usuario.email)
                .where(Usuario.funcionario_id.in_(func_ids))
            )
            emails_func = {row[0]: row[1] for row in rows}

        out: list[MovimentoOut] = [
            MovimentoOut(
                id=r["id"],
                tipo=r["tipo"],
                produto_id=r.get("produto_id"),
                produto_nome=nomes_produto.get(r["produto_id"]) if r.get("produto_id") else None,
                lote_id=r.get("lote_id"),
                quantidade=float(r["quantidade"]),
                data_movimento=r["data_movimento"],
                preco=float(r["preco"]) if r.get("preco") is not None else None,
                funcionario_id=r.get("funcionario_id"),
                responsavel_email=emails_func.get(r["funcionario_id"]) if r.get("funcionario_id") else None,
            )
            for r in linhas
        ]
        return PaginatedResponse.build(out, total, page, size)