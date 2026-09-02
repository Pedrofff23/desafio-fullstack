"""DTOs do módulo de usuários e funcionários.

O cadastro exige nome, e-mail, contato e endereço (com integração IBGE:
o frontend seleciona o estado e, em seguida, a cidade correspondente).
"""

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.localidade import CidadeOut


class ContatoBase(BaseModel):
    """Telefone/contato."""

    codigo_pais: str = Field("+55", max_length=4, examples=["+55"])
    ddd: str = Field(..., min_length=2, max_length=2, examples=["11"])
    numero: str = Field(..., min_length=8, max_length=15, examples=["999991234"])


class ContatoIn(ContatoBase):
    @field_validator("ddd")
    @classmethod
    def _ddd_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("DDD deve conter apenas dígitos")
        return v

    @field_validator("numero")
    @classmethod
    def _numero_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Número deve conter apenas dígitos")
        return v


class EnderecoBase(BaseModel):
    """Endereço ligado ao IBGE (cidade -> estado)."""

    logradouro: str = Field(..., min_length=1, max_length=150)
    numero: str = Field(..., min_length=1, max_length=20)
    complemento: str | None = Field(None, max_length=100)
    cep: str = Field(..., min_length=8, max_length=8, examples=["01001000"])
    bairro: str = Field(..., min_length=1, max_length=100)


class EnderecoIn(EnderecoBase):
    """Endereço informado no cadastro/edição."""

    estado_id: int = Field(..., description="ID do estado (UF) escolhido (IBGE)")
    cidade_id: int = Field(..., description="ID da cidade escolhida (IBGE)")

    @field_validator("cep")
    @classmethod
    def _cep_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CEP deve conter apenas dígitos")
        return v


class EnderecoOut(EnderecoBase):
    id: int
    cidade: CidadeOut

    model_config = {"from_attributes": True}


class ContatoOut(ContatoBase):
    id: int

    model_config = {"from_attributes": True}


class FuncionarioOut(BaseModel):
    """Dados do funcionário vinculado ao usuário."""

    id: int
    nome_completo: str
    data_cadastro: object
    ativo: bool
    endereco: EnderecoOut
    contato: ContatoOut

    model_config = {"from_attributes": True}


class UsuarioOut(BaseModel):
    """Saída completa de um usuário (listagem/detalhe)."""

    id: int
    email: EmailStr
    perfil: str
    ativo: bool
    data_cadastro: object
    funcionario: FuncionarioOut

    model_config = {"from_attributes": True}


class UsuarioResumo(BaseModel):
    """Usuário resumido usado em respostas de auditoria (ex.: responsável)."""

    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    """Cadastro de usuário: nome, e-mail, senha, contato e endereço (IBGE)."""

    nome: str = Field(..., min_length=2, max_length=150, description="Nome completo")
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=128)
    perfil: str = Field("funcionario", pattern="^(admin|funcionario)$")
    contato: ContatoIn
    endereco: EnderecoIn

    @field_validator("email")
    @classmethod
    def _normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()


class UsuarioUpdate(BaseModel):
    """Edição de usuário (nome, e-mail, contato e endereço)."""

    nome: str | None = Field(None, min_length=2, max_length=150)
    email: EmailStr | None = None
    senha: str | None = Field(None, min_length=6, max_length=128)
    perfil: str | None = Field(None, pattern="^(admin|funcionario)$")
    ativo: bool | None = None
    contato: ContatoIn | None = None
    endereco: EnderecoIn | None = None

    @field_validator("email")
    @classmethod
    def _normalizar_email(cls, valor: EmailStr | None) -> str | None:
        return str(valor).strip().lower() if valor is not None else None
