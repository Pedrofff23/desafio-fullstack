"""Service de produtos, lotes e catálogo.

Responsável por montar a listagem com saldo de estoque e alertas visuais
(validade próxima < 30 dias, estoque baixo/zerado), além do CRUD.
"""

from datetime import date
from typing import cast

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.produto import Lote, Produto
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.produto import (
    CategoriaOut,
    LoteCreate,
    LoteOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
    UnidadeMedidaOut,
)

# Limiar em dias para considerar validade "próxima do vencimento".
LIMIAR_VALIDADE_DIAS = 30
LIMIAR_ESTOQUE_BAIXO = 5
STATUS_VALIDOS = {"ok", "validade_proxima", "vencido", "estoque_baixo", "zerado"}


class ProdutoService:
    """Regras de negócio do módulo de produtos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProdutoRepository(session)

    # ------------------------------------------------------------------
    # Montagem do DTO de listagem com alertas
    # ------------------------------------------------------------------
    def _enriquecer(
        self,
        produto: Produto,
        quantidade: float = 0,
        data_validade: date | None = None,
    ) -> ProdutoOut:
        status = "ok"
        if data_validade is not None:
            dias = (data_validade - date.today()).days
            if dias < 0:
                status = "vencido"
            elif dias < LIMIAR_VALIDADE_DIAS:
                status = "validade_proxima"
        if status == "ok" and quantidade <= 0:
            status = "zerado"
        elif status == "ok" and quantidade < LIMIAR_ESTOQUE_BAIXO:
            status = "estoque_baixo"

        return ProdutoOut(
            id=produto.id,
            codigo=produto.codigo,
            nome=produto.nome,
            descricao=produto.descricao,
            preco=float(produto.preco),
            perecivel=produto.perecivel,
            unidade_medida_id=produto.unidade_medida_id,
            categoria_id=produto.categoria_id,
            localizacao_id=produto.localizacao_id,
            ativo=produto.ativo,
            unidade_medida=UnidadeMedidaOut.model_validate(
                produto.unidade_medida, from_attributes=True
            )
            if produto.unidade_medida
            else None,
            categoria=CategoriaOut.model_validate(
                produto.categoria, from_attributes=True
            )
            if produto.categoria
            else None,
            quantidade_estoque=quantidade,
            data_validade=data_validade,
            status=status,
        )

    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    async def catalogo(self) -> dict:
        unidades = await self.repo.list_unidades()
        categorias = await self.repo.list_categorias()
        localizacoes = await self.repo.list_localizacoes()
        return {
            "unidades_medida": unidades,
            "categorias": categorias,
            "localizacoes": localizacoes,
        }

    # ------------------------------------------------------------------
    # Listagem com filtros
    # ------------------------------------------------------------------
    async def listar(
        self,
        page: int = 1,
        size: int = 20,
        nome: str | None = None,
        status: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> PaginatedResponse[ProdutoOut]:
        if preco_min is not None and preco_max is not None and preco_min > preco_max:
            raise HTTPException(status_code=422, detail="Preço mínimo maior que o máximo")
        if status is not None and status not in STATUS_VALIDOS:
            raise HTTPException(status_code=422, detail="Status de produto inválido")
        itens = await self.repo.listar_filtros(
            nome=nome, preco_min=preco_min, preco_max=preco_max
        )
        estatisticas = await self.repo.estatisticas_produtos([p.id for p in itens])
        out = [
            self._enriquecer(
                p,
                *cast(
                    tuple[float, date | None],
                    estatisticas.get(p.id, (0.0, None)),
                ),
            )
            for p in itens
        ]
        if status is not None:
            out = [produto for produto in out if produto.status == status]
        total = len(out)
        inicio = (page - 1) * size
        return PaginatedResponse.build(out[inicio : inicio + size], total, page, size)

    async def obter(self, produto_id: int) -> ProdutoOut:
        produto = await self.repo.get_com_relacionamentos(produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        estatisticas = await self.repo.estatisticas_produtos([produto.id])
        quantidade, data_validade = cast(
            tuple[float, date | None], estatisticas.get(produto.id, (0.0, None))
        )
        return self._enriquecer(
            produto, quantidade, data_validade
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def criar(self, data: ProdutoCreate, funcionario_id: int) -> ProdutoOut:
        if await self.repo.get_by_codigo(data.codigo):
            raise HTTPException(status_code=409, detail="Código de produto já existe")
        if not await self.repo.validar_referencias(
            data.unidade_medida_id, data.categoria_id, data.localizacao_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Unidade, categoria ou localização informada não existe",
            )
        lote_inicial = data.lote_inicial
        produto = Produto(
            **data.model_dump(exclude={"lote_inicial"}),
            funcionario_id=funcionario_id,
        )
        try:
            await self.repo.add(produto)
            if lote_inicial is not None:
                self.session.add(
                    Lote(produto_id=produto.id, **lote_inicial.model_dump())
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Produto ou lote já cadastrado"
            ) from exc
        return await self.obter(produto.id)

    async def atualizar(
        self, produto_id: int, data: ProdutoUpdate
    ) -> ProdutoOut:
        produto = await self.repo.get_com_relacionamentos(produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        valores = data.model_dump(exclude_unset=True)
        codigo = valores.get("codigo")
        if codigo is not None and codigo != produto.codigo:
            existente = await self.repo.get_by_codigo(codigo)
            if existente is not None:
                raise HTTPException(status_code=409, detail="Código de produto já existe")
        if not await self.repo.validar_referencias(
            valores.get("unidade_medida_id", produto.unidade_medida_id),
            valores.get("categoria_id", produto.categoria_id),
            valores.get("localizacao_id", produto.localizacao_id),
        ):
            raise HTTPException(
                status_code=400,
                detail="Unidade, categoria ou localização informada não existe",
            )
        for k, v in valores.items():
            setattr(produto, k, v)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Não foi possível atualizar o produto"
            ) from exc
        return await self.obter(produto_id)

    async def excluir(self, produto_id: int, excluido_por: int | None = None) -> None:
        produto = await self.repo.get(produto_id)
        if produto is None or produto.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        await self.repo.soft_delete(produto_id, excluido_por)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Lotes
    # ------------------------------------------------------------------
    async def criar_lote(
        self, produto_id: int, data: LoteCreate, excluido_por: int | None = None
    ) -> LoteOut:
        produto = await self.repo.get(produto_id)
        if produto is None or produto.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        if produto.perecivel and data.data_validade is None:
            raise HTTPException(
                status_code=422,
                detail="Produto perecível exige data de validade no lote",
            )
        lote = Lote(produto_id=produto_id, **data.model_dump())
        try:
            self.session.add(lote)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(status_code=409, detail="Número de lote já cadastrado") from exc
        return LoteOut.model_validate(lote, from_attributes=True)

    async def listar_lotes(self, produto_id: int) -> list[LoteOut]:
        produto = await self.repo.get(produto_id)
        if produto is None or produto.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        lotes = await self.repo.list_lotes_do_produto(produto_id)
        return [
            LoteOut.model_validate(l, from_attributes=True) for l in lotes
        ]
