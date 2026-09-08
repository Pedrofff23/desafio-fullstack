"""Rotas do CRUD de fornecedores."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import SUPPLIERS_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate
from app.services.fornecedor_service import FornecedorService

router = APIRouter(prefix="/transacoes/fornecedores")


@router.get(
    "",
    response_model=list[FornecedorOut],
    tags=[SUPPLIERS_TAG],
    summary="Listar fornecedores",
)
async def listar(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[FornecedorOut]:
    return await FornecedorService(db).listar()


@router.post(
    "",
    response_model=FornecedorOut,
    status_code=status.HTTP_201_CREATED,
    tags=[SUPPLIERS_TAG],
    summary="Cadastrar fornecedor",
)
async def criar(
    payload: FornecedorCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).criar(payload)


@router.get(
    "/{fornecedor_id}",
    response_model=FornecedorOut,
    tags=[SUPPLIERS_TAG],
    summary="Obter fornecedor",
)
async def obter(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).obter(fornecedor_id)


@router.put(
    "/{fornecedor_id}",
    response_model=FornecedorOut,
    tags=[SUPPLIERS_TAG],
    summary="Atualizar fornecedor",
)
async def atualizar(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).atualizar(fornecedor_id, payload)


@router.delete(
    "/{fornecedor_id}",
    response_model=MessageResponse,
    tags=[SUPPLIERS_TAG],
    summary="Excluir fornecedor",
)
async def excluir(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MessageResponse:
    await FornecedorService(db).excluir(fornecedor_id, current.id)
    return MessageResponse(message="Fornecedor excluído com sucesso.")
