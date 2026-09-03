"""DTOs do módulo de produtos, lotes e catálogo."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UnidadeMedidaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla: str
    descricao: str


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None


class IngredienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None


class AlergenoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None


class LocalizacaoOut(BaseModel):
    id: int
    prateleira_id: int
    corredor: str
    seccao: str
    prateleira: str
    nivel: int | None = None
    descricao: str | None = None


class NutrienteInput(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    unidade: str = Field(min_length=1, max_length=10)
    valor: float = Field(ge=0)


class NutrienteOut(NutrienteInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProdutoIngredienteInput(BaseModel):
    ingrediente_id: int
    ordem: int = Field(gt=0)


class ProdutoIngredienteOut(ProdutoIngredienteInput):
    nome: str
    descricao: str | None = None


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


class ProdutoCreate(BaseModel):
    """Cadastro de produto (código único, nome, categoria, unidade, localização)."""

    codigo: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=2, max_length=150)
    descricao: str | None = None
    preco: float = Field(ge=0)
    perecivel: bool = False
    unidade_medida_id: int
    categoria_id: int
    localizacao_id: int
    ativo: bool = True
    lote_inicial: LoteInput | None = None
    nutrientes: list[NutrienteInput] = Field(default_factory=list)
    ingredientes: list[ProdutoIngredienteInput] = Field(default_factory=list)
    alergeno_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validade_obrigatoria_para_perecivel(self) -> "ProdutoCreate":
        if self.perecivel and (
            self.lote_inicial is None or self.lote_inicial.data_validade is None
        ):
            raise ValueError(
                "Produto perecível exige lote inicial com data de validade"
            )
        self._validar_composicao()
        return self

    def _validar_composicao(self) -> None:
        nomes = [item.nome.strip().casefold() for item in self.nutrientes]
        if len(nomes) != len(set(nomes)):
            raise ValueError("Os nomes dos nutrientes não podem se repetir")
        ingrediente_ids = [item.ingrediente_id for item in self.ingredientes]
        ordens = [item.ordem for item in self.ingredientes]
        if len(ingrediente_ids) != len(set(ingrediente_ids)):
            raise ValueError("O mesmo ingrediente não pode ser selecionado duas vezes")
        if len(ordens) != len(set(ordens)):
            raise ValueError("A ordem dos ingredientes não pode se repetir")
        if len(self.alergeno_ids) != len(set(self.alergeno_ids)):
            raise ValueError("O mesmo alérgeno não pode ser selecionado duas vezes")


class ProdutoUpdate(BaseModel):
    """Edição de produto. A data de validade NÃO reside aqui (é do lote)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = None
    preco: float | None = Field(default=None, ge=0)
    unidade_medida_id: int | None = None
    categoria_id: int | None = None
    localizacao_id: int | None = None
    ativo: bool | None = None
    nutrientes: list[NutrienteInput] | None = None
    ingredientes: list[ProdutoIngredienteInput] | None = None
    alergeno_ids: list[int] | None = None

    @model_validator(mode="after")
    def _composicao_sem_repeticoes(self) -> "ProdutoUpdate":
        if self.nutrientes is not None:
            nomes = [item.nome.strip().casefold() for item in self.nutrientes]
            if len(nomes) != len(set(nomes)):
                raise ValueError("Os nomes dos nutrientes não podem se repetir")
        if self.ingredientes is not None:
            ingrediente_ids = [item.ingrediente_id for item in self.ingredientes]
            ordens = [item.ordem for item in self.ingredientes]
            if len(ingrediente_ids) != len(set(ingrediente_ids)):
                raise ValueError(
                    "O mesmo ingrediente não pode ser selecionado duas vezes"
                )
            if len(ordens) != len(set(ordens)):
                raise ValueError("A ordem dos ingredientes não pode se repetir")
        if self.alergeno_ids is not None and len(self.alergeno_ids) != len(
            set(self.alergeno_ids)
        ):
            raise ValueError("O mesmo alérgeno não pode ser selecionado duas vezes")
        return self


class ProdutoOut(BaseModel):
    """Produto com relacionamentos e saldo de estoque para listagem."""

    model_config = ConfigDict(from_attributes=True)

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
    quantidade_estoque: float = 0
    status: Literal["ok", "estoque_baixo", "zerado"] = "ok"
    total_lotes: int = 0
    nutrientes: list[NutrienteOut] = Field(default_factory=list)
    ingredientes: list[ProdutoIngredienteOut] = Field(default_factory=list)
    alergenos: list[AlergenoOut] = Field(default_factory=list)


class LoteCreate(LoteInput):
    """Criação de lote (validade é propriedade do lote)."""


class LoteLocalizacaoOut(LocalizacaoOut):
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


class ListaCatalogo(BaseModel):
    """Catálogo de unidades e categorias para os selects do frontend."""

    unidades_medida: list[UnidadeMedidaOut]
    categorias: list[CategoriaOut]
    localizacoes: list[LocalizacaoOut]
    ingredientes: list[IngredienteOut]
    alergenos: list[AlergenoOut]
