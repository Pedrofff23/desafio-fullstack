"""DTOs do módulo de produtos, lotes e catálogo."""

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class UnidadeMedidaOut(BaseModel):
    id: int
    sigla: str
    descricao: str

    model_config = {"from_attributes": True}


class CategoriaOut(BaseModel):
    id: int
    nome: str
    descricao: str | None

    model_config = {"from_attributes": True}


class LocalizacaoOut(BaseModel):
    id: int
    prateleira_id: int

    model_config = {"from_attributes": True}


class ProdutoCreate(BaseModel):
    """Cadastro de produto (código único, nome, categoria, unidade, localização)."""

    codigo: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=2, max_length=150)
    descricao: str | None = None
    unidade_medida_id: int
    categoria_id: int
    localizacao_id: int
    ativo: bool = True


class ProdutoUpdate(BaseModel):
    """Edição de produto. A data de validade NÃO reside aqui (é do lote)."""

    codigo: str | None = Field(None, min_length=1, max_length=50)
    nome: str | None = Field(None, min_length=2, max_length=150)
    descricao: str | None = None
    unidade_medida_id: int | None = None
    categoria_id: int | None = None
    localizacao_id: int | None = None
    ativo: bool | None = None


class ProdutoOut(BaseModel):
    """Produto com relacionamentos e saldo de estoque para listagem."""

    id: int
    codigo: str
    nome: str
    descricao: str | None
    unidade_medida_id: int
    categoria_id: int
    localizacao_id: int | None = None
    ativo: bool
    unidade_medida: UnidadeMedidaOut | None = None
    categoria: CategoriaOut | None = None
    # Campos preenchidos no service para a listagem do frontend:
    quantidade_estoque: float = 0
    preco: float | None = None
    data_validade: date | None = None
    status: str = "ok"  # ok | validade_proxima | vencido | estoque_baixo | zerado

    model_config = {"from_attributes": True}


class LoteCreate(BaseModel):
    """Criação de lote (validade é propriedade do lote)."""

    numero_lote: str = Field(..., min_length=1, max_length=50)
    data_producao: date
    data_validade: date = Field(..., description="Data de validade do lote")
    ativo: bool = True

    @model_validator(mode="after")
    def _validade_apos_producao(self) -> "LoteCreate":
        if self.data_validade < self.data_producao:
            raise ValueError("Data de validade não pode ser anterior à produção")
        return self


class LoteOut(BaseModel):
    id: int
    produto_id: int
    numero_lote: str
    data_producao: date
    data_validade: date
    ativo: bool

    model_config = {"from_attributes": True}


class ListaCatalogo(BaseModel):
    """Catálogo de unidades e categorias para os selects do frontend."""

    unidades_medida: list[UnidadeMedidaOut]
    categorias: list[CategoriaOut]
    localizacoes: list[LocalizacaoOut]