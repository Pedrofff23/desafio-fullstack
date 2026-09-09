"""Repositório do CRUD de fornecedores."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fornecedor import Fornecedor
from app.models.localidade import Endereco
from app.repositories.base import BaseRepository


class FornecedorRepository(BaseRepository[Fornecedor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Fornecedor, session)

    def _com_relacionamentos(self):
        return select(Fornecedor).options(
            selectinload(Fornecedor.contato),
            selectinload(Fornecedor.endereco).selectinload(Endereco.cidade),
        )

    async def list(self) -> list[Fornecedor]:
        result = await self.session.execute(
            self._com_relacionamentos()
            .where(Fornecedor.excluido_em.is_(None))
            .order_by(Fornecedor.nome_empresa)
        )
        return list(result.scalars().unique().all())

    async def get(self, id: int) -> Fornecedor | None:
        result = await self.session.execute(
            self._com_relacionamentos().where(
                Fornecedor.id == id,
                Fornecedor.excluido_em.is_(None),
            )
        )
        return result.scalars().unique().one_or_none()
