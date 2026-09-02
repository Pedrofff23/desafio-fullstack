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
    UsuarioResumo,
    UsuarioUpdate,
)

__all__ = [
    "CategoriaOut",
    "CidadeOut",
    "EstadoOut",
    "EstoqueEntradaOut",
    "EstoqueProdutoOut",
    "FornecedorCreate",
    "FornecedorOut",
    "ListaCatalogo",
    "LocalizacaoOut",
    "LoginRequest",
    "LoteCreate",
    "LoteOut",
    "MessageResponse",
    "MovimentoOut",
    "PaginatedResponse",
    "ProdutoCreate",
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
