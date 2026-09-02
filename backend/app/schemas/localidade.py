"""DTOs de localidades (IBGE): estados e cidades."""

from pydantic import BaseModel, Field


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
    estado_id: int | None = Field(validation_alias="uf")

    model_config = {"from_attributes": True, "populate_by_name": True}
