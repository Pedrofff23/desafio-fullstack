"""Re-exporta os repositórios (Repository Pattern)."""

from app.repositories.base import BaseRepository
from app.repositories.fornecedor_repository import FornecedorRepository
from app.repositories.localidade_repository import LocalidadeRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.transacao_repository import TransacaoRepository
from app.repositories.usuario_repository import UsuarioRepository

__all__ = [
    "BaseRepository",
    "FornecedorRepository",
    "LocalidadeRepository",
    "LoteRepository",
    "ProdutoRepository",
    "TransacaoRepository",
    "UsuarioRepository",
]
