"""Rotas de CRUD de usuários."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import USERS_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=[USERS_TAG])


@router.get("", response_model=PaginatedResponse[UsuarioOut], summary="Listar usuários")
async def listar(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    nome: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await UsuarioService(db).listar(page=page, size=size, nome=nome)


@router.post(
    "", response_model=UsuarioOut, status_code=201, summary="Cadastrar usuário"
)
async def criar(
    payload: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return await UsuarioService(db).criar(payload, criado_por=current.id)


@router.get("/{usuario_id}", response_model=UsuarioOut, summary="Obter usuário")
async def obter(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await UsuarioService(db).obter(usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioOut, summary="Atualizar usuário")
async def atualizar(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return await UsuarioService(db).atualizar(usuario_id, payload, current.id)


@router.delete(
    "/{usuario_id}", response_model=MessageResponse, summary="Excluir usuário"
)
async def excluir(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    await UsuarioService(db).excluir(usuario_id, excluido_por=current.id)
    return MessageResponse(message="Usuário excluído com sucesso.")
