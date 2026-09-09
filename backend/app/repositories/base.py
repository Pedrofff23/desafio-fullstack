"""Repositório genérico base (Repository Pattern).

Fornece operações CRUD fundamentais e suporte a exclusão lógica (soft delete),
quando o modelo expõe as colunas de auditoria `excluido_em`/`excluido_por`.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.base import Base


class BaseRepository[ModelT: Base]:
    """Operações genéricas sobre um modelo ORM."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    async def get(self, id: int) -> ModelT | None:
        return await self.session.get(self.model, id)

    def _active_stmt(self) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        excluido_em = getattr(self.model, "excluido_em", None)
        if excluido_em is not None:
            stmt = stmt.where(excluido_em.is_(None))
        return stmt

    async def list_all(self, *, exclude_deleted: bool = True) -> list[ModelT]:
        stmt = self._active_stmt() if exclude_deleted else select(self.model)
        result = await self.session.execute(
            stmt.order_by(getattr(self.model, "id"))
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Persistência / Exclusão
    # ------------------------------------------------------------------
    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def soft_delete(
        self, id: int, deleted_by: int | None = None
    ) -> ModelT | None:
        """Marca como excluído se o modelo suportar soft delete."""
        obj = await self.get(id)
        if obj is None:
            return None
        if hasattr(obj, "excluido_em"):
            setattr(obj, "excluido_em", datetime.now(UTC))
            if deleted_by is not None and hasattr(obj, "excluido_por"):
                setattr(obj, "excluido_por", deleted_by)
            await self.session.flush()
        else:
            await self.session.delete(obj)
            await self.session.flush()
        return obj
