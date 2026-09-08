"""Rotas do CRUD de lotes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import LOTS_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse
from app.schemas.lote import LoteCreate, LoteOut, LoteUpdate
from app.services.lote_service import LoteService

router = APIRouter(prefix="/produtos/{produto_id}/lotes")


@router.get(
    "",
    response_model=list[LoteOut],
    tags=[LOTS_TAG],
    summary="Listar lotes de um produto",
)
async def listar(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> list[LoteOut]:
    return await LoteService(db).listar(produto_id)


@router.post(
    "",
    response_model=LoteOut,
    status_code=status.HTTP_201_CREATED,
    tags=[LOTS_TAG],
    summary="Cadastrar lote de um produto",
)
async def criar(
    produto_id: int,
    payload: LoteCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> LoteOut:
    return await LoteService(db).criar(produto_id, payload)


@router.get(
    "/{lote_id}",
    response_model=LoteOut,
    tags=[LOTS_TAG],
    summary="Obter lote de um produto",
)
async def obter(
    produto_id: int,
    lote_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> LoteOut:
    return await LoteService(db).obter(produto_id, lote_id)


@router.put(
    "/{lote_id}",
    response_model=LoteOut,
    tags=[LOTS_TAG],
    summary="Atualizar lote de um produto",
)
async def atualizar(
    produto_id: int,
    lote_id: int,
    payload: LoteUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> LoteOut:
    return await LoteService(db).atualizar(produto_id, lote_id, payload)


@router.delete(
    "/{lote_id}",
    response_model=MessageResponse,
    tags=[LOTS_TAG],
    summary="Excluir lote de um produto",
)
async def excluir(
    produto_id: int,
    lote_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MessageResponse:
    await LoteService(db).excluir(produto_id, lote_id, current.id)
    return MessageResponse(message="Lote excluído com sucesso.")
