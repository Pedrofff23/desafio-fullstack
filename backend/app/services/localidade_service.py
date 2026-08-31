"""Service de localidades (IBGE): estados e cidades."""

from fastapi import HTTPException

from app.repositories.localidade_repository import LocalidadeRepository
from app.schemas.localidade import CidadeOut, EstadoOut


class LocalidadeService:
    """Regras de negócio para a consulta de dados IBGE."""

    def __init__(self, session) -> None:
        self.repo = LocalidadeRepository(session)

    async def listar_estados(self) -> list[EstadoOut]:
        estados = await self.repo.list_estados()
        return [
            EstadoOut(id=e.id, nome=e.nome, uf=e.uf, ibge=e.ibge) for e in estados
        ]

    async def listar_cidades_do_estado(self, estado_id: int) -> list[CidadeOut]:
        estado = await self.repo.get_estado(estado_id)
        if estado is None:
            raise HTTPException(status_code=404, detail="Estado não encontrado")
        cidades = await self.repo.list_cidades_por_estado(estado_id)
        return [
            CidadeOut(id=c.id, nome=c.nome, ibge=c.ibge) for c in cidades
        ]