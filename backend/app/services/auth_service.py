"""Service de autenticação: login e emissão de JWT."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    """Regras de negócio de autenticação."""

    def __init__(self, session) -> None:
        self.repo = UsuarioRepository(session)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        usuario = await self.repo.get_by_email_including_inactive(
            str(payload.email).strip().lower()
        )
        if usuario is None:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        if not usuario.ativo or usuario.excluido_em is not None:
            raise HTTPException(status_code=401, detail="Usuário inativo ou excluído")
        if not verify_password(payload.senha, usuario.senha_hash):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        expira = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        token = create_access_token(subject=usuario.id, expires_minutes=expira)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expira * 60,
        )
