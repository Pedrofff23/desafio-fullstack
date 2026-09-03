"""DTOs de movimentações de estoque, fornecedores e saldos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.usuario import ContatoIn, ContatoOut, EnderecoIn, EnderecoOut

# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------


class FornecedorCreate(BaseModel):
    """Cadastro de fornecedor."""

    nome_empresa: str = Field(..., min_length=2, max_length=150)
    contato: ContatoIn
    endereco: EnderecoIn
    ativo: bool = True


class FornecedorOut(BaseModel):
    id: int
    nome_empresa: str
    ativo: bool
    data_cadastro: datetime
    contato: ContatoOut
    endereco: EnderecoOut

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
    data_entrada: datetime | None = None
    tipo_entrada: str = Field("compra", min_length=1, max_length=50)
    observacao: str | None = Field(None, max_length=500)
    preco_custo: float = Field(..., ge=0)


class RegistroEntradaOut(BaseModel):
    id: int
    lote_id: int
    fornecedor_id: int
    localizacao_id: int
    quantidade: float
    data_entrada: datetime
    tipo_entrada: str
    observacao: str | None
    preco_custo: float
    funcionario_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Saídas
# ---------------------------------------------------------------------------


class RegistroSaidaCreate(BaseModel):
    """Saída de estoque (vinculada a uma entrada com saldo disponível)."""

    entrada_id: int
    quantidade: float = Field(..., gt=0)
    data_saida: datetime | None = None
    tipo_saida: str = Field("venda", min_length=1, max_length=50)
    preco_venda: float = Field(..., ge=0)


class RegistroSaidaOut(BaseModel):
    id: int
    entrada_id: int
    quantidade: float
    data_saida: datetime
    tipo_saida: str
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
    tipo_movimento: str
    produto_id: int | None = None
    produto_nome: str | None = None
    lote_id: int | None = None
    quantidade: float
    data_movimento: datetime
    preco: float | None = None
    observacao: str | None = None
    funcionario_id: int | None = None
    responsavel_email: str | None = None


class EstoqueProdutoOut(BaseModel):
    """Saldo atual de cada produto (view estoque_produto)."""

    produto_id: int
    produto_nome: str
    quantidade: float
    total_lotes: int = 0
    lotes_vencendo: int = 0
    lotes_vencidos: int = 0


class EstoqueEntradaOut(BaseModel):
    """Saldo por entrada (view estoque_entrada)."""

    entrada_id: int
    lote_id: int
    produto_id: int
    fornecedor_id: int
    localizacao_id: int
    quantidade: float
