"""Re-exporta os DTOs (camada de dados de transferência)."""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate
from app.schemas.localidade import CidadeOut, EstadoOut
from app.schemas.lote import LoteCreate, LoteLocalizacaoOut, LoteOut, LoteUpdate
from app.schemas.produto import (
    AlergenoOut,
    CategoriaOut,
    IngredienteOut,
    ListaCatalogo,
    LocalizacaoOut,
    NutrienteInput,
    NutrienteOut,
    ProdutoCreate,
    ProdutoIngredienteInput,
    ProdutoIngredienteOut,
    ProdutoOut,
    ProdutoUpdate,
    UnidadeMedidaOut,
)
from app.schemas.transacao import (
    EstoqueEntradaOut,
    EstoqueProdutoOut,
    MovimentoOut,
    RegistroEntradaCreate,
    RegistroEntradaOut,
    RegistroSaidaCreate,
    RegistroSaidaOut,
)
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioOut,
    UsuarioResumo,
    UsuarioUpdate,
)

__all__ = [
    "AlergenoOut",
    "CategoriaOut",
    "CidadeOut",
    "EstadoOut",
    "EstoqueEntradaOut",
    "EstoqueProdutoOut",
    "FornecedorCreate",
    "FornecedorOut",
    "FornecedorUpdate",
    "IngredienteOut",
    "ListaCatalogo",
    "LocalizacaoOut",
    "LoginRequest",
    "LoteCreate",
    "LoteLocalizacaoOut",
    "LoteOut",
    "LoteUpdate",
    "MessageResponse",
    "MovimentoOut",
    "PaginatedResponse",
    "NutrienteInput",
    "NutrienteOut",
    "ProdutoCreate",
    "ProdutoIngredienteInput",
    "ProdutoIngredienteOut",
    "ProdutoOut",
    "ProdutoUpdate",
    "RegistroEntradaCreate",
    "RegistroEntradaOut",
    "RegistroSaidaCreate",
    "RegistroSaidaOut",
    "TokenResponse",
    "UnidadeMedidaOut",
    "UsuarioCreate",
    "UsuarioOut",
    "UsuarioResumo",
    "UsuarioUpdate",
]
