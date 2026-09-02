"""Re-exporta os repositórios (Repository Pattern)."""

from app.repositories.base import BaseRepository
from app.repositories.localidade_repository import LocalidadeRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.transacao_repository import TransacaoRepository
from app.repositories.usuario_repository import UsuarioRepository

__all__ = [
    "BaseRepository",
    "LocalidadeRepository",
    "ProdutoRepository",
    "TransacaoRepository",
    "UsuarioRepository",
]
