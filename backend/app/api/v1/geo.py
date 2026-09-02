"""Rotas de localidades (IBGE): estados e cidades."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.localidade import CidadeOut, EstadoOut
from app.services.localidade_service import LocalidadeService

router = APIRouter(prefix="/geo", tags=["Localidades (IBGE)"])


@router.get("/estados", response_model=list[EstadoOut])
async def listar_estados(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await LocalidadeService(db).listar_estados()


@router.get("/estados/{estado_id}/cidades", response_model=list[CidadeOut])
async def listar_cidades(
    estado_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await LocalidadeService(db).listar_cidades_do_estado(estado_id)
