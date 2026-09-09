"""Repositório de produtos e catálogos auxiliares."""

from sqlalchemy import BigInteger, and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lote import Lote
from app.models.produto import (
    Alergeno,
    Categoria,
    Ingrediente,
    LocalizacaoEstoque,
    Prateleira,
    Produto,
    ProdutoAlergeno,
    ProdutoIngrediente,
    Seccao,
    UnidadeMedida,
)
from app.repositories.base import BaseRepository

LIMIAR_ESTOQUE_BAIXO = 5


class ProdutoRepository(BaseRepository[Produto]):
    """Acesso a dados de produtos e entidades do catálogo."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Produto, session)

    async def get_for_update(self, produto_id: int) -> Produto | None:
        result = await self.session.execute(
            select(Produto)
            .where(Produto.id == produto_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Produto | None:
        stmt = select(Produto).where(Produto.codigo == codigo)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_com_relacionamentos(self, produto_id: int) -> Produto | None:
        result = await self.session.execute(
            select(Produto)
            .where(Produto.id == produto_id, Produto.excluido_em.is_(None))
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
                selectinload(Produto.nutrientes),
                selectinload(Produto.ingredientes_associacoes).selectinload(
                    ProdutoIngrediente.ingrediente
                ),
                selectinload(Produto.alergenos_associacoes).selectinload(
                    ProdutoAlergeno.alergeno
                ),
            )
        )
        return result.scalars().unique().one_or_none()

    async def list_paginated(
        self,
        *,
        page: int = 1,
        size: int = 20,
        nome: str | None = None,
        status: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> tuple[list[Produto], int, dict[int, float], dict[int, int]]:
        """Listagem paginada de produtos com filtros e saldos calculados em SQL."""
        estoque_subq = (
            select(
                func.cast(text("produto_id"), BigInteger).label("produto_id"),
                func.coalesce(func.sum(text("quantidade")), 0).label("saldo"),
            )
            .select_from(text("estoque_produto"))
            .group_by(text("produto_id"))
            .subquery("sub_estoque")
        )
        saldo_col = func.coalesce(estoque_subq.c.saldo, 0)

        base_stmt = (
            select(Produto.id, saldo_col.label("saldo"))
            .outerjoin(estoque_subq, estoque_subq.c.produto_id == Produto.id)
            .where(Produto.excluido_em.is_(None))
        )
        if nome:
            base_stmt = base_stmt.where(Produto.nome.ilike(f"%{nome.strip()}%"))
        if preco_min is not None:
            base_stmt = base_stmt.where(Produto.preco >= preco_min)
        if preco_max is not None:
            base_stmt = base_stmt.where(Produto.preco <= preco_max)
        if status == "zerado":
            base_stmt = base_stmt.where(saldo_col <= 0)
        elif status == "estoque_baixo":
            base_stmt = base_stmt.where(
                and_(saldo_col > 0, saldo_col < LIMIAR_ESTOQUE_BAIXO)
            )
        elif status == "ok":
            base_stmt = base_stmt.where(saldo_col >= LIMIAR_ESTOQUE_BAIXO)

        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = int(await self.session.scalar(total_stmt) or 0)
        if total == 0:
            return [], 0, {}, {}

        paged_id_stmt = (
            base_stmt.order_by(Produto.nome, Produto.id)
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await self.session.execute(paged_id_stmt)).all()
        p_ids = [int(r[0]) for r in rows]
        saldos = {int(r[0]): float(r[1]) for r in rows}

        stmt = (
            select(Produto)
            .where(Produto.id.in_(p_ids))
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
                selectinload(Produto.nutrientes),
                selectinload(Produto.ingredientes_associacoes).selectinload(
                    ProdutoIngrediente.ingrediente
                ),
                selectinload(Produto.alergenos_associacoes).selectinload(
                    ProdutoAlergeno.alergeno
                ),
            )
            .order_by(Produto.nome, Produto.id)
        )
        result = await self.session.execute(stmt)
        produtos = list(result.scalars().unique().all())

        lotes_counts = await self.count_product_lots(p_ids)
        return produtos, total, saldos, lotes_counts

    async def validate_references(
        self, unidade_medida_id: int, categoria_id: int, localizacao_id: int
    ) -> bool:
        unidade = await self.session.get(UnidadeMedida, unidade_medida_id)
        categoria = await self.session.get(Categoria, categoria_id)
        localizacao = await self.session.get(LocalizacaoEstoque, localizacao_id)
        return unidade is not None and categoria is not None and localizacao is not None

    async def list_unidades(self) -> list[UnidadeMedida]:
        result = await self.session.execute(
            select(UnidadeMedida).order_by(UnidadeMedida.sigla)
        )
        return list(result.scalars().all())

    async def list_categorias(self) -> list[Categoria]:
        result = await self.session.execute(select(Categoria).order_by(Categoria.nome))
        return list(result.scalars().all())

    async def list_localizacoes(self) -> list[LocalizacaoEstoque]:
        result = await self.session.execute(
            select(LocalizacaoEstoque)
            .options(
                selectinload(LocalizacaoEstoque.prateleira)
                .selectinload(Prateleira.seccao)
                .selectinload(Seccao.corredor)
            )
            .order_by(LocalizacaoEstoque.id)
        )
        return list(result.scalars().all())

    async def list_ingredientes(self) -> list[Ingrediente]:
        result = await self.session.execute(
            select(Ingrediente).order_by(Ingrediente.nome)
        )
        return list(result.scalars().all())

    async def list_alergenos(self) -> list[Alergeno]:
        result = await self.session.execute(select(Alergeno).order_by(Alergeno.nome))
        return list(result.scalars().all())

    async def validate_food_references(
        self, ingrediente_ids: set[int], alergeno_ids: set[int]
    ) -> bool:
        if ingrediente_ids:
            encontrados = await self.session.scalar(
                select(func.count(Ingrediente.id)).where(
                    Ingrediente.id.in_(ingrediente_ids)
                )
            )
            if int(encontrados or 0) != len(ingrediente_ids):
                return False
        if alergeno_ids:
            encontrados = await self.session.scalar(
                select(func.count(Alergeno.id)).where(Alergeno.id.in_(alergeno_ids))
            )
            if int(encontrados or 0) != len(alergeno_ids):
                return False
        return True

    async def add_lote(self, lote: Lote) -> Lote:
        self.session.add(lote)
        await self.session.flush()
        return lote

    async def get_localizacao(self, localizacao_id: int) -> LocalizacaoEstoque | None:
        return await self.session.get(LocalizacaoEstoque, localizacao_id)

    async def get_product_balances(self, produto_ids: list[int]) -> dict[int, float]:
        """Retorna o saldo total dos produtos sem criar outra fonte de verdade."""
        if not produto_ids:
            return {}
        saldos_rows = await self.session.execute(
            text("""
                SELECT produto_id, COALESCE(SUM(quantidade), 0)
                FROM estoque_produto
                WHERE produto_id = ANY(CAST(:produto_ids AS bigint[]))
                GROUP BY produto_id
                """),
            {"produto_ids": produto_ids},
        )
        return {int(row[0]): float(row[1]) for row in saldos_rows.fetchall()}

    async def count_product_lots(self, produto_ids: list[int]) -> dict[int, int]:
        """Retorna a contagem de lotes não excluídos de cada produto."""
        if not produto_ids:
            return {}
        rows = await self.session.execute(
            select(Lote.produto_id, func.count(Lote.id))
            .where(
                Lote.produto_id.in_(produto_ids),
                Lote.excluido_em.is_(None),
            )
            .group_by(Lote.produto_id)
        )
        return {int(row[0]): int(row[1]) for row in rows.all()}
