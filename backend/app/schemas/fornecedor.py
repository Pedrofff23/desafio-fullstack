"""DTOs do CRUD de fornecedores."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.usuario import ContatoIn, ContatoOut, EnderecoIn, EnderecoOut


class FornecedorCreate(BaseModel):
    nome_empresa: str = Field(min_length=2, max_length=150)
    contato: ContatoIn
    endereco: EnderecoIn
    ativo: bool = True


class FornecedorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome_empresa: str | None = Field(default=None, min_length=2, max_length=150)
    contato: ContatoIn | None = None
    endereco: EnderecoIn | None = None
    ativo: bool | None = None


class FornecedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_empresa: str
    ativo: bool
    data_cadastro: datetime
    contato: ContatoOut
    endereco: EnderecoOut
