"""Re-exporta todos os models para que sejam registrados no Base.metadata.

Importar `app.models` garante que todas as tabelas sejam conhecidas pelo
Alembic (autogenerate) e pelo `Base.metadata.create_all`.
"""

from app.models.base import Base
from app.models.localidade import Cidade, Contato, Endereco, Estado, Pais
from app.models.produto import (
    Alergeno,
    Categoria,
    Corredor,
    Ingrediente,
    LocalizacaoEstoque,
    Lote,
    Nutriente,
    Prateleira,
    Produto,
    ProdutoAlergeno,
    ProdutoIngrediente,
    Seccao,
    UnidadeMedida,
)
from app.models.transacao import Fornecedor, RegistroEntrada, RegistroSaida
from app.models.usuario import Funcionario, Sessao, Usuario

__all__ = [
    "Base",
    "Pais",
    "Estado",
    "Cidade",
    "Endereco",
    "Contato",
    "Funcionario",
    "Usuario",
    "Sessao",
    "Fornecedor",
    "UnidadeMedida",
    "Categoria",
    "Alergeno",
    "Ingrediente",
    "Corredor",
    "Seccao",
    "Prateleira",
    "LocalizacaoEstoque",
    "Produto",
    "Lote",
    "Nutriente",
    "ProdutoIngrediente",
    "ProdutoAlergeno",
    "RegistroEntrada",
    "RegistroSaida",
]
