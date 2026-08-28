"""Service de produtos, lotes e catálogo.

Responsável por montar a listagem com saldo de estoque e alertas visuais
(validade próxima < 30 dias, estoque baixo/zerado), além do CRUD.
"""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.produto import Lote, Produto
from app.models.transacao import RegistroEntrada
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


class ProdutoService:
    """Regras de negócio do módulo de produtos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProdutoRepository(session)

    # ------------------------------------------------------------------
    # Montagem do DTO de listagem com alertas
    # ------------------------------------------------------------------
    async def _enriquecer(self, produto: Produto) -> ProdutoOut:
        quantidade = await self.repo.saldo_produto(produto.id)

        # Validade mais próxima (lote ativo)
        lotes = await self.repo.list_lotes_do_produto(produto.id)
        data_validade = None
        preco = None
        for lote in lotes:
            if data_validade is None or lote.data_validade < data_validade:
                data_validade = lote.data_validade

        # Preço sugerido mais recente (primeira entrada de um lote ativo)
        if lotes:
            from app.models.transacao import RegistroEntrada

            ultimo_lote = lotes[0]
            ultima_entrada = await self.session.execute(
                select(RegistroEntrada)
                .where(RegistroEntrada.lote_id == ultimo_lote.id)
                .order_by(RegistroEntrada.data_entrada.desc())
            )
            entrada = ultima_entrada.scalar_one_or_none()
            if entrada is not None:
                preco = float(entrada.preco_sugerido)

        status = "ok"
        if quantidade <= 0:
            status = "zerado"
        elif quantidade < 5:
            status = "estoque_baixo"
        if data_validade is not None:
            dias = (data_validade - date.today()).days
            if dias < 0:
                status = "vencido"
            elif dias < LIMIAR_VALIDADE_DIAS:
                status = "validade_proxima"

        return ProdutoOut(
            id=produto.id,
            codigo=produto.codigo,
            nome=produto.nome,
            descricao=produto.descricao,
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
            preco=preco,
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
        itens, total = await self.repo.list_paginated_filtros(
            page=page,
            size=size,
            nome=nome,
            status=status,
            preco_min=preco_min,
            preco_max=preco_max,
        )
        out = [await self._enriquecer(p) for p in itens]
        return PaginatedResponse.build(out, total, page, size)

    async def obter(self, produto_id: int) -> ProdutoOut:
        stmt = (
            select(Produto)
            .where(Produto.id == produto_id, Produto.excluido_em.is_(None))
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
            )
        )
        result = await self.session.execute(stmt)
        produto = result.scalars().unique().one_or_none()
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return await self._enriquecer(produto)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def criar(self, data: ProdutoCreate, funcionario_id: int) -> ProdutoOut:
        if await self.repo.get_by_codigo(data.codigo):
            raise HTTPException(status_code=409, detail="Código de produto já existe")
        produto = Produto(
            **data.model_dump(), funcionario_id=funcionario_id
        )
        produto = await self.repo.add(produto)
        await self.session.commit()
        
        # Recarregar com eager loading
        stmt = (
            select(Produto)
            .where(Produto.id == produto.id)
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
            )
        )
        result = await self.session.execute(stmt)
        produto = result.scalars().unique().one()
        return await self._enriquecer(produto)

    async def atualizar(
        self, produto_id: int, data: ProdutoUpdate
    ) -> ProdutoOut:
        stmt = (
            select(Produto)
            .where(Produto.id == produto_id, Produto.excluido_em.is_(None))
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
            )
        )
        result = await self.session.execute(stmt)
        produto = result.scalars().unique().one_or_none()
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(produto, k, v)
        await self.session.commit()
        
        # Recarregar com eager loading
        stmt = (
            select(Produto)
            .where(Produto.id == produto_id)
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
            )
        )
        result = await self.session.execute(stmt)
        produto = result.scalars().unique().one()
        return await self._enriquecer(produto)

    async def excluir(self, produto_id: int, excluido_por: int | None = None) -> None:
        produto = await self.repo.get(produto_id)
        if produto is None:
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
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        lote = Lote(produto_id=produto_id, **data.model_dump())
        lote = await self.repo.add(lote)
        await self.session.commit()
        return LoteOut.model_validate(lote, from_attributes=True)

    async def listar_lotes(self, produto_id: int) -> list[LoteOut]:
        lotes = await self.repo.list_lotes_do_produto(produto_id)
        return [
            LoteOut.model_validate(l, from_attributes=True) for l in lotes
        ]