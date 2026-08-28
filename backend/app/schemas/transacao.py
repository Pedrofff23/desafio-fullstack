"""DTOs de movimentações de estoque, fornecedores e saldos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------

class FornecedorCreate(BaseModel):
    """Cadastro de fornecedor."""

    nome_empresa: str = Field(..., min_length=2, max_length=150)
    ativo: bool = True


class FornecedorOut(BaseModel):
    id: int
    nome_empresa: str
    ativo: bool
    data_cadastro: object

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------

class RegistroEntradaCreate(BaseModel):
    """Registro de entrada de estoque (associada a um lote)."""

    lote_id: int
    fornecedor_id: int
    localizacao_id: int | None = Field(
        None, description="Se omitida, usa a localização preferencial do produto"
    )
    quantidade: float = Field(..., gt=0)
    preco_custo: float = Field(..., ge=0)
    preco_sugerido: float = Field(..., ge=0)


class RegistroEntradaOut(BaseModel):
    id: int
    lote_id: int
    fornecedor_id: int
    localizacao_id: int
    quantidade: float
    data_entrada: datetime
    preco_custo: float
    preco_sugerido: float
    funcionario_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Saídas
# ---------------------------------------------------------------------------

class RegistroSaidaCreate(BaseModel):
    """Saída de estoque (vinculada a uma entrada com saldo disponível)."""

    entrada_id: int
    quantidade: float = Field(..., gt=0)
    preco_venda: float = Field(..., ge=0)


class RegistroSaidaOut(BaseModel):
    id: int
    entrada_id: int
    quantidade: float
    data_saida: datetime
    preco_venda: float
    funcionario_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Histórico e saldos
# ---------------------------------------------------------------------------

class MovimentoOut(BaseModel):
    """Linha do histórico de transações (auditoria: quem, quando, o quê)."""

    id: int
    tipo: Literal["entrada", "saida"]
    produto_id: int | None = None
    produto_nome: str | None = None
    lote_id: int | None = None
    quantidade: float
    data_movimento: datetime
    preco: float | None = None
    funcionario_id: int | None = None
    responsavel_email: str | None = None


class EstoqueProdutoOut(BaseModel):
    """Saldo atual de cada produto (view estoque_produto)."""

    lote_id: int
    produto_id: int
    quantidade: float


class EstoqueEntradaOut(BaseModel):
    """Saldo por entrada (view estoque_entrada)."""

    entrada_id: int
    lote_id: int
    produto_id: int
    fornecedor_id: int
    localizacao_id: int
    quantidade: float