"""Repositório de produtos, lotes e catálogo."""

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.produto import (
    Categoria,
    LocalizacaoEstoque,
    Lote,
    Produto,
    UnidadeMedida,
)
from app.repositories.base import BaseRepository


class ProdutoRepository(BaseRepository[Produto]):
    """Acesso a dados de produtos e entidades do catálogo."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Produto, session)

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
            )
        )
        return result.scalars().unique().one_or_none()

    async def listar_filtros(
        self,
        *,
        nome: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> list[Produto]:
        stmt = (
            select(Produto)
            .where(Produto.excluido_em.is_(None))
            .options(
                selectinload(Produto.unidade_medida),
                selectinload(Produto.categoria),
            )
            .order_by(Produto.nome, Produto.id)
        )
        if nome:
            stmt = stmt.where(Produto.nome.ilike(f"%{nome.strip()}%"))
        if preco_min is not None:
            stmt = stmt.where(Produto.preco >= preco_min)
        if preco_max is not None:
            stmt = stmt.where(Produto.preco <= preco_max)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def validar_referencias(
        self, unidade_medida_id: int, categoria_id: int, localizacao_id: int
    ) -> bool:
        unidade = await self.session.get(UnidadeMedida, unidade_medida_id)
        categoria = await self.session.get(Categoria, categoria_id)
        localizacao = await self.session.get(LocalizacaoEstoque, localizacao_id)
        return unidade is not None and categoria is not None and localizacao is not None

    async def list_paginated_filtros(
        self,
        *,
        page: int = 1,
        size: int = 20,
        nome: str | None = None,
        status: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> tuple[list[Produto], int]:
        """Lista produtos com filtros de nome, status e intervalo de preço."""

        base = select(Produto).where(Produto.excluido_em.is_(None))
        count_stmt = select(func.count(Produto.id)).where(
            Produto.excluido_em.is_(None)
        )

        if nome:
            like = f"%{nome.lower()}%"
            base = base.where(func.lower(Produto.nome).like(like))

        # Filtros de status e preço exigem junção com estoque/lotes (saldo e preço).
        # Preço: usa o preço_sugerido mais recente do primeiro lote ativo com
        # entrada; status: derivado de validade e saldo no service (simplificado
        # aqui apenas com o preço, os alertas de status são calculados no service).
        if preco_min is not None or preco_max is not None:
            sub = (
                select(Lote.produto_id, func.max(Lote.id).label("lote_id"))
                .group_by(Lote.produto_id)
                .subquery()
            )
            # Junta com o estoque real por produto (estatística agregada)
            from app.models.transacao import RegistroEntrada

            preco_sub = (
                select(
                    RegistroEntrada.lote_id,
                    func.max(RegistroEntrada.preco_sugerido).label("preco"),
                )
                .group_by(RegistroEntrada.lote_id)
                .subquery()
            )
            base = base.join(sub, sub.c.produto_id == Produto.id).join(
                preco_sub, preco_sub.c.lote_id == sub.c.lote_id
            )
            if preco_min is not None:
                base = base.where(preco_sub.c.preco >= preco_min)
            if preco_max is not None:
                base = base.where(preco_sub.c.preco <= preco_max)

        result = await self.session.execute(base.offset((page - 1) * size).limit(size))
        items = list(result.scalars().unique().all())

        total = await self.session.execute(count_stmt)
        total = int(total.scalar() or 0)
        return items, total

    async def list_unidades(self) -> list[UnidadeMedida]:
        result = await self.session.execute(select(UnidadeMedida).order_by(UnidadeMedida.sigla))
        return list(result.scalars().all())

    async def list_categorias(self) -> list[Categoria]:
        result = await self.session.execute(select(Categoria).order_by(Categoria.nome))
        return list(result.scalars().all())

    async def list_localizacoes(self) -> list[LocalizacaoEstoque]:
        result = await self.session.execute(
            select(LocalizacaoEstoque).order_by(LocalizacaoEstoque.id)
        )
        return list(result.scalars().all())

    async def get_lote(self, lote_id: int) -> Lote | None:
        return await self.session.get(Lote, lote_id)

    async def list_lotes_do_produto(self, produto_id: int) -> list[Lote]:
        result = await self.session.execute(
            select(Lote)
            .where(Lote.produto_id == produto_id, Lote.excluido_em.is_(None))
            .order_by(Lote.data_validade.asc().nulls_last(), Lote.id)
        )
        return list(result.scalars().all())

    async def estatisticas_produtos(
        self, produto_ids: list[int]
    ) -> dict[int, tuple[float, object | None]]:
        """Retorna saldo e validade mais próxima sem consultas N+1."""
        if not produto_ids:
            return {}
        saldos_rows = await self.session.execute(
            text(
                """
                SELECT produto_id, COALESCE(SUM(quantidade), 0)
                FROM estoque_produto
                GROUP BY produto_id
                """
            )
        )
        saldos = {int(row[0]): float(row[1]) for row in saldos_rows.fetchall()}
        validades_rows = await self.session.execute(
            text(
                """
                SELECT ep.produto_id, MIN(l.data_validade)
                FROM estoque_produto ep
                JOIN lotes l ON l.id = ep.lote_id
                WHERE ep.quantidade > 0
                  AND l.ativo = TRUE
                  AND l.excluido_em IS NULL
                  AND l.data_validade IS NOT NULL
                GROUP BY ep.produto_id
                """
            )
        )
        validades = {int(row[0]): row[1] for row in validades_rows.fetchall()}
        return {
            produto_id: (saldos.get(produto_id, 0.0), validades.get(produto_id))
            for produto_id in produto_ids
        }

    # ------------------------------------------------------------------
    # Saldo / estoque (via as views criadas na migration)
    # ------------------------------------------------------------------
    async def saldo_produto(self, produto_id: int) -> float:
        row = await self.session.execute(
            text(
                """
                SELECT COALESCE(SUM(quantidade), 0)
                FROM estoque_produto
                WHERE produto_id = :pid
                """
            ),
            {"pid": produto_id},
        )
        return float(row.scalar() or 0)

    async def saldo_lote(self, lote_id: int) -> float:
        row = await self.session.execute(
            text(
                """
                SELECT COALESCE(SUM(quantidade), 0)
                FROM estoque_produto
                WHERE lote_id = :lid
                """
            ),
            {"lid": lote_id},
        )
        return float(row.scalar() or 0)
