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


class LoteInput(BaseModel):
    numero_lote: str = Field(..., min_length=1, max_length=50)
    data_producao: date
    data_validade: date | None = None
    ativo: bool = True

    @model_validator(mode="after")
    def _validade_apos_producao(self) -> "LoteInput":
        if self.data_validade is not None and self.data_validade < self.data_producao:
            raise ValueError("Data de validade não pode ser anterior à produção")
        return self


class ProdutoCreate(BaseModel):
    """Cadastro de produto (código único, nome, categoria, unidade, localização)."""

    codigo: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=2, max_length=150)
    descricao: str | None = None
    preco: float = Field(..., ge=0)
    perecivel: bool = False
    unidade_medida_id: int
    categoria_id: int
    localizacao_id: int
    ativo: bool = True
    lote_inicial: LoteInput | None = None

    @model_validator(mode="after")
    def _validade_obrigatoria_para_perecivel(self) -> "ProdutoCreate":
        if self.perecivel and (
            self.lote_inicial is None or self.lote_inicial.data_validade is None
        ):
            raise ValueError(
                "Produto perecível exige lote inicial com data de validade"
            )
        return self


class ProdutoUpdate(BaseModel):
    """Edição de produto. A data de validade NÃO reside aqui (é do lote)."""

    model_config = {"extra": "forbid"}

    codigo: str | None = Field(None, min_length=1, max_length=50)
    nome: str | None = Field(None, min_length=2, max_length=150)
    descricao: str | None = None
    preco: float | None = Field(None, ge=0)
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
    preco: float
    perecivel: bool
    unidade_medida_id: int
    categoria_id: int
    localizacao_id: int | None = None
    ativo: bool
    unidade_medida: UnidadeMedidaOut | None = None
    categoria: CategoriaOut | None = None
    # Campos preenchidos no service para a listagem do frontend:
    quantidade_estoque: float = 0
    data_validade: date | None = None
    status: str = "ok"  # ok | validade_proxima | vencido | estoque_baixo | zerado

    model_config = {"from_attributes": True}


class LoteCreate(LoteInput):
    """Criação de lote (validade é propriedade do lote)."""

    pass


class LoteOut(BaseModel):
    id: int
    produto_id: int
    numero_lote: str
    data_producao: date
    data_validade: date | None
    ativo: bool

    model_config = {"from_attributes": True}


class ListaCatalogo(BaseModel):
    """Catálogo de unidades e categorias para os selects do frontend."""

    unidades_medida: list[UnidadeMedidaOut]
    categorias: list[CategoriaOut]
    localizacoes: list[LocalizacaoOut]
