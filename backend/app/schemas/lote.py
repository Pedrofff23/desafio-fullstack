"""DTOs do CRUD de lotes."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoteInput(BaseModel):
    numero_lote: str = Field(min_length=1, max_length=50)
    data_producao: date
    data_validade: date | None = None
    ativo: bool = True

    @model_validator(mode="after")
    def _validade_apos_producao(self) -> "LoteInput":
        if self.data_validade is not None and self.data_validade < self.data_producao:
            raise ValueError("Data de validade não pode ser anterior à produção")
        return self


class LoteCreate(LoteInput):
    pass


class LoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero_lote: str | None = Field(default=None, min_length=1, max_length=50)
    data_producao: date | None = None
    data_validade: date | None = None
    ativo: bool | None = None


class LoteLocalizacaoOut(BaseModel):
    id: int
    prateleira_id: int
    corredor: str
    seccao: str
    prateleira: str
    nivel: int | None = None
    descricao: str | None = None
    quantidade: float


class LoteOut(BaseModel):
    id: int
    produto_id: int
    numero_lote: str
    data_producao: date
    data_validade: date | None
    ativo: bool
    quantidade_estoque: float = 0
    status_estoque: Literal["com_estoque", "sem_estoque"] = "sem_estoque"
    dias_para_vencer: int | None = None
    status_validade: Literal[
        "normal", "validade_proxima", "vencido", "sem_validade"
    ] = "sem_validade"
    localizacoes: list[LoteLocalizacaoOut] = Field(default_factory=list)
