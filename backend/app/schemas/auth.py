"""DTOs de autenticação: login e token."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credenciais para autenticação."""

    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Token JWT retornado após autenticação."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
