"""Repositório genérico base (Repository Pattern).

Fornece operações CRUD comuns e suporte a exclusão lógica (soft delete),
quando o modelo expõe as colunas de auditoria `excluido_em`/`excluido_por`.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Operações genéricas sobre um modelo ORM."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    async def get(self, id: int) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def get_or_none(self, **filters) -> ModelT | None:
        stmt = select(self.model)
        for col, value in filters.items():
            stmt = stmt.where(getattr(self.model, col) == value)
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    def _active_stmt(self) -> Select:
        stmt = select(self.model)
        if hasattr(self.model, "excluido_em"):
            stmt = stmt.where(self.model.excluido_em.is_(None))
        return stmt

    async def list_all(self, *, exclude_deleted: bool = True) -> list[ModelT]:
        stmt = self._active_stmt() if exclude_deleted else select(self.model)
        result = await self.session.execute(stmt.order_by(self.model.id))
        return list(result.scalars().all())

    async def list_paginated(
        self,
        *,
        page: int = 1,
        size: int = 20,
        filters: dict | None = None,
        order_by=None,
    ) -> tuple[list[ModelT], int]:
        """Retorna (itens, total) aplicando paginação e filtros simples."""
        from sqlalchemy import func as sa_func

        base = self._active_stmt()
        params = [filters] if isinstance(filters, dict) else (filters or [])
        for f in params:
            for col, value in f.items():
                attr = getattr(self.model, col, None)
                if attr is not None and value is not None:
                    base = base.where(attr == value)

        # Conta usando o mesmo stmt filtrado — sem acessar APIs internas do SQLAlchemy
        count_stmt = select(sa_func.count()).select_from(base.subquery())
        total_row = await self.session.execute(count_stmt)
        total = int(total_row.scalar() or 0)

        if order_by is not None:
            base = base.order_by(order_by)
        else:
            base = base.order_by(self.model.id)

        base = base.offset((page - 1) * size).limit(size)
        result = await self.session.execute(base)
        return list(result.scalars().all()), total

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------
    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete_hard(self, id: int) -> None:
        obj = await self.get(id)
        if obj is not None:
            await self.session.delete(obj)
            await self.session.flush()

    async def soft_delete(
        self, id: int, deleted_by: int | None = None
    ) -> ModelT | None:
        """Marca como excluído se o modelo suportar soft delete."""
        obj = await self.get(id)
        if obj is None:
            return None
        if hasattr(obj, "excluido_em"):
            from datetime import UTC, datetime

            obj.excluido_em = datetime.now(UTC)
            if deleted_by is not None and hasattr(obj, "excluido_por"):
                obj.excluido_por = deleted_by
            await self.session.flush()
        else:
            await self.session.delete(obj)
            await self.session.flush()
        return obj
