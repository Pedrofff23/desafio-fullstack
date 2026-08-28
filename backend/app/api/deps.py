"""Dependências da API: autenticação e obtenção de sessão/usuário corrente."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Resolve o usuário autenticado a partir do token JWT (Bearer)."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UsuarioRepository(db)
    usuario = await repo.get(int(subject))
    if usuario is None or usuario.excluido_em is not None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou inexistente",
        )
    return usuario


def require_admin(current: Usuario = Depends(get_current_user)) -> Usuario:
    """Garante que o usuário corrente tenha perfil de administrador."""
    if current.perfil != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores",
        )
    return current