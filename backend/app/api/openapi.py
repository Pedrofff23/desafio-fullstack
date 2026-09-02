"""Metadados compartilhados da documentação OpenAPI."""

SYSTEM_TAG = "Sistema"
AUTH_TAG = "Autenticação"
GEO_TAG = "Localidades"
USERS_TAG = "Usuários"
CATALOGS_TAG = "Catálogos auxiliares"
PRODUCTS_TAG = "Produtos"
LOTS_TAG = "Lotes"
SUPPLIERS_TAG = "Fornecedores"
INVENTORY_MOVEMENTS_TAG = "Movimentações de estoque"
INVENTORY_QUERIES_TAG = "Consultas de estoque"

API_DESCRIPTION = """
API para gerenciamento de produtos, lotes e movimentações de estoque.

As operações protegidas exigem um token Bearer obtido na seção **Autenticação**.
A validade pertence ao lote, enquanto o saldo é calculado a partir das entradas e
saídas registradas.
"""

OPENAPI_TAGS = [
    {
        "name": SYSTEM_TAG,
        "description": "Disponibilidade da aplicação e conexão com o banco de dados.",
    },
    {
        "name": AUTH_TAG,
        "description": "Autenticação e identificação do usuário conectado.",
    },
    {
        "name": GEO_TAG,
        "description": "Estados e cidades utilizados nos endereços do sistema.",
    },
    {
        "name": USERS_TAG,
        "description": "Cadastro e manutenção dos usuários e funcionários.",
    },
    {
        "name": CATALOGS_TAG,
        "description": (
            "Dados auxiliares usados no cadastro de produtos, como categorias, "
            "unidades, localizações, ingredientes e alérgenos."
        ),
    },
    {
        "name": PRODUCTS_TAG,
        "description": "Cadastro comercial, classificação e composição dos produtos.",
    },
    {
        "name": LOTS_TAG,
        "description": (
            "Lotes pertencentes aos produtos, incluindo validade, saldo e localização."
        ),
    },
    {
        "name": SUPPLIERS_TAG,
        "description": "Cadastro e consulta dos fornecedores das entradas de estoque.",
    },
    {
        "name": INVENTORY_MOVEMENTS_TAG,
        "description": "Registro das entradas e saídas que alteram o estoque.",
    },
    {
        "name": INVENTORY_QUERIES_TAG,
        "description": "Consulta de saldos, entradas disponíveis e histórico do estoque.",
    },
]
