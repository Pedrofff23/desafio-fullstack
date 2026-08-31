"""Re-exporta os DTOs (camada de dados de transferência)."""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.localidade import CidadeOut, EstadoOut
from app.schemas.produto import (
    CategoriaOut,
    ListaCatalogo,
    LocalizacaoOut,
    LoteCreate,
    LoteOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
    UnidadeMedidaOut,
)
from app.schemas.transacao import (
    EstoqueEntradaOut,
    EstoqueProdutoOut,
    FornecedorCreate,
    FornecedorOut,
    MovimentoOut,
    RegistroEntradaCreate,
    RegistroEntradaOut,
    RegistroSaidaCreate,
    RegistroSaidaOut,
)
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioOut,
    UsuarioUpdate,
    UsuarioResumo,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "MessageResponse",
    "PaginatedResponse",
    "EstadoOut",
    "CidadeOut",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioOut",
    "UsuarioResumo",
    "UnidadeMedidaOut",
    "CategoriaOut",
    "LocalizacaoOut",
    "ListaCatalogo",
    "ProdutoCreate",
    "ProdutoUpdate",
    "ProdutoOut",
    "LoteCreate",
    "LoteOut",
    "FornecedorCreate",
    "FornecedorOut",
    "RegistroEntradaCreate",
    "RegistroEntradaOut",
    "RegistroSaidaCreate",
    "RegistroSaidaOut",
    "MovimentoOut",
    "EstoqueProdutoOut",
    "EstoqueEntradaOut",
]