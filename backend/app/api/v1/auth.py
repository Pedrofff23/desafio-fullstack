"""Rotas de autenticação."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import AUTH_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioOut
from app.services.auth_service import AuthService
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=[AUTH_TAG])


@router.post("/login", response_model=TokenResponse, summary="Autenticar usuário")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(payload)


@router.get("/me", response_model=UsuarioOut, summary="Obter usuário autenticado")
async def me(
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return await UsuarioService(db).me(current.id)
