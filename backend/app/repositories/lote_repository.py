"""Repositório do CRUD de lotes e seus saldos/localizações."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote import Lote
from app.repositories.base import BaseRepository


class LoteRepository(BaseRepository[Lote]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Lote, session)

    async def get(
        self, id: int, lote_id: int | None = None
    ) -> Lote | None:
        """Obtém um lote por id ou por (produto_id, lote_id)."""
        if lote_id is None:
            # Chamada com apenas lote_id (ex: transacao_service)
            stmt = select(Lote).where(
                Lote.id == id,
                Lote.excluido_em.is_(None),
            )
        else:
            # Chamada com produto_id e lote_id (ex: lote_service)
            stmt = select(Lote).where(
                Lote.id == lote_id,
                Lote.produto_id == id,
                Lote.excluido_em.is_(None),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_produto(self, produto_id: int) -> list[Lote]:
        result = await self.session.execute(
            select(Lote)
            .where(Lote.produto_id == produto_id, Lote.excluido_em.is_(None))
            .order_by(Lote.data_validade.asc().nulls_last(), Lote.id)
        )
        return list(result.scalars().all())

    async def saldo(self, lote_id: int) -> float:
        result = await self.session.execute(
            text(
                "SELECT COALESCE(SUM(quantidade), 0) FROM estoque_produto WHERE lote_id = :lote_id"
            ),
            {"lote_id": lote_id},
        )
        return float(result.scalar() or 0)

    async def localizacoes(self, produto_id: int) -> dict[int, list[dict[str, Any]]]:
        rows = await self.session.execute(
            text("""
                SELECT ee.lote_id, ee.localizacao_id, le.prateleira_id,
                       cr.nome AS corredor, s.nome AS seccao, pr.nome AS prateleira,
                       pr.nivel, pr.descricao, SUM(ee.quantidade) AS quantidade
                FROM estoque_entrada ee
                JOIN localizacoes_estoque le ON le.id = ee.localizacao_id
                JOIN prateleiras pr ON pr.id = le.prateleira_id
                JOIN seccoes s ON s.id = pr.seccao_id
                JOIN corredores cr ON cr.id = s.corredor_id
                WHERE ee.produto_id = :produto_id AND ee.quantidade > 0
                GROUP BY ee.lote_id, ee.localizacao_id, le.prateleira_id,
                         cr.nome, s.nome, pr.nome, pr.nivel, pr.descricao
                ORDER BY ee.lote_id, cr.nome, s.nome, pr.nome
            """),
            {"produto_id": produto_id},
        )
        result: dict[int, list[dict[str, Any]]] = {}
        for row in rows.mappings():
            result.setdefault(int(row["lote_id"]), []).append(
                {
                    "id": int(row["localizacao_id"]),
                    "prateleira_id": int(row["prateleira_id"]),
                    "corredor": row["corredor"],
                    "seccao": row["seccao"],
                    "prateleira": row["prateleira"],
                    "nivel": row["nivel"],
                    "descricao": row["descricao"],
                    "quantidade": float(row["quantidade"]),
                }
            )
        return result
