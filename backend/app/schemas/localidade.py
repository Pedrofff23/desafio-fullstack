"""DTOs de localidades (IBGE): estados e cidades."""

from pydantic import BaseModel, ConfigDict, Field


class EstadoOut(BaseModel):
    """Estado (UF) para select do frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str | None
    uf: str | None
    ibge: int | None


class CidadeOut(BaseModel):
    """Cidade para select do frontend (filtrada por estado)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    nome: str | None
    ibge: int | None
    estado_id: int | None = Field(default=None, validation_alias="uf")
