"""Rotas de localidades (IBGE): estados e cidades."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import GEO_TAG
from app.core.database import get_db
from app.schemas.localidade import CidadeOut, EstadoOut
from app.services.localidade_service import LocalidadeService

router = APIRouter(prefix="/geo", tags=[GEO_TAG])


@router.get(
    "/estados",
    status_code=status.HTTP_200_OK,
    summary="Listar estados",
)
async def listar_estados(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[EstadoOut]:
    return await LocalidadeService(db).listar_estados()


@router.get(
    "/estados/{estado_id}/cidades",
    response_model=list[CidadeOut],
    status_code=status.HTTP_200_OK,
    summary="Listar cidades de um estado",
)
async def listar_cidades(
    estado_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[CidadeOut]:
    return await LocalidadeService(db).listar_cidades_do_estado(estado_id)
