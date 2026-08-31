"""DTOs de localidades (IBGE): estados e cidades."""

from pydantic import BaseModel


class EstadoOut(BaseModel):
    """Estado (UF) para select do frontend."""

    id: int
    nome: str | None
    uf: str | None
    ibge: int | None

    model_config = {"from_attributes": True}


class CidadeOut(BaseModel):
    """Cidade para select do frontend (filtrada por estado)."""

    id: int
    nome: str | None
    ibge: int | None

    model_config = {"from_attributes": True}