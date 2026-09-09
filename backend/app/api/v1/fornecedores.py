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
async def list_suppliers(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[FornecedorOut]:
    return await FornecedorService(db).list()


@router.post(
    "",
    response_model=FornecedorOut,
    status_code=status.HTTP_201_CREATED,
    tags=[SUPPLIERS_TAG],
    summary="Cadastrar fornecedor",
)
async def create_supplier(
    payload: FornecedorCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).create(payload)


@router.get(
    "/{fornecedor_id}",
    response_model=FornecedorOut,
    tags=[SUPPLIERS_TAG],
    summary="Obter fornecedor",
)
async def get_supplier(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).get(fornecedor_id)


@router.put(
    "/{fornecedor_id}",
    response_model=FornecedorOut,
    tags=[SUPPLIERS_TAG],
    summary="Atualizar fornecedor",
)
async def update_supplier(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await FornecedorService(db).update(fornecedor_id, payload)


@router.delete(
    "/{fornecedor_id}",
    response_model=MessageResponse,
    tags=[SUPPLIERS_TAG],
    summary="Excluir fornecedor",
)
async def delete_supplier(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MessageResponse:
    await FornecedorService(db).delete(fornecedor_id, current.id)
    return MessageResponse(message="Fornecedor excluído com sucesso.")
