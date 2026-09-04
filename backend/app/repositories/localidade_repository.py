"""Repositório de localidades (IBGE): países, estados e cidades."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.localidade import Cidade, Estado, Pais
from app.repositories.base import BaseRepository


class LocalidadeRepository(BaseRepository[Estado]):
    """Acesso a dados geográficos IBGE."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Estado, session)

    async def list_paises(self) -> list[Pais]:
        result = await self.session.execute(select(Pais).order_by(Pais.nome))
        return list(result.scalars().all())

    async def list_estados(self) -> list[Estado]:
        return await self.list_all(exclude_deleted=False)

    async def list_cidades_por_estado(self, estado_id: int) -> list[Cidade]:
        result = await self.session.execute(
            select(Cidade).where(Cidade.uf == estado_id).order_by(Cidade.nome)
        )
        return list(result.scalars().all())

    async def get_cidade(self, cidade_id: int) -> Cidade | None:
        return await self.session.get(Cidade, cidade_id)

    async def get_estado(self, estado_id: int) -> Estado | None:
        return await self.session.get(Estado, estado_id)

    async def cidade_pertence_ao_estado(self, cidade_id: int, estado_id: int) -> bool:
        result = await self.session.execute(
            select(Cidade.id).where(Cidade.id == cidade_id, Cidade.uf == estado_id)
        )
        return result.scalar_one_or_none() is not None
