"""Seed do banco de dados.

Carrega os dados de referência (unidades de medida, categorias, alergenos,
ingredientes, localizações de estoque) e cria o usuário administrador inicial.

Os dados geográficos IBGE (paises, estados, cidades) são carregados pelo
script `scripts/seed_geo.sh` (via psql), que lida com os dumps COPY.

Uso (dentro do container backend):
    python -m scripts.init_db
"""

import asyncio
import logging
import os

from sqlalchemy import text

from app.core.database import db_manager
from app.core.security import hash_password

logger = logging.getLogger("estoque.seed")

# Dados de referência — cada INSERT é executado separadamente (asyncpg não
# aceita múltiplos statements em um único prepared statement).
REFERENCE_INSERTS: list[str] = [
    """
    INSERT INTO unidades_medida (sigla, descricao) VALUES
        ('kg',  'Quilograma'), ('g', 'Grama'), ('mg', 'Miligrama'),
        ('kcal','Quilocaloria'), ('l', 'Litro'), ('ml', 'Mililitro'),
        ('un',  'Unidade'), ('cx', 'Caixa'), ('fr', 'Frasco'), ('pct', 'Pacote')
    ON CONFLICT (sigla) DO NOTHING
    """,
    """
    INSERT INTO categorias (nome, descricao) VALUES
        ('Laticínios',  'Produtos derivados de leite'),
        ('Bebidas',     'Bebidas e refrigerantes'),
        ('Carnes',      'Carnes bovina, frango, suína, etc.'),
        ('Hortifrúti',  'Frutas, verduras e hortaliças'),
        ('Padaria',     'Pães, bolos e produtos de padaria'),
        ('Limpeza',     'Produtos de limpeza e higiene'),
        ('Congelados',  'Produtos congelados'),
        ('Enlatados',   'Produtos enlatados e conservas'),
        ('Doces',       'Doces e confeitarias'),
        ('Bebidas Alcoólicas', 'Cervejas, vinhos e destilados')
    ON CONFLICT (nome) DO NOTHING
    """,
    """
    INSERT INTO alergenos (nome, descricao) VALUES
        ('Glúten',        'Encontrado em trigo, centeio, cevada, entre outros'),
        ('Lactose',       'Encontrada no leite e derivados'),
        ('Soja',          'Encontrada em produtos de soja e derivados'),
        ('Nozes',         'Encontradas em nozes, castanhas e amêndoas'),
        ('Ovos',          'Encontrados em ovos de galinha e derivados'),
        ('Frutos do Mar', 'Crustáceos e moluscos'),
        ('Cenoura',       'Alergia a cenoura (OGM ou alérgico)')
    ON CONFLICT (nome) DO NOTHING
    """,
    """
    INSERT INTO ingredientes (nome, descricao) VALUES
        ('Leite',              'Leite de vaca integral'),
        ('Açúcar',             'Açúcar refinado'),
        ('Farinha de Trigo',   'Farinha de trigo comum'),
        ('Ovos',               'Ovos de galinha caipiras'),
        ('Fermento',           'Fermento químico em pó'),
        ('Óleo Vegetal',       'Óleo de soja ou canola'),
        ('Água',               'Água potável'),
        ('Sal',                'Sal comum')
    ON CONFLICT (nome) DO NOTHING
    """,
]


async def seed_referencia(session) -> None:
    """Carrega dados de referência (unidades, categorias, etc.)."""
    for stmt in REFERENCE_INSERTS:
        await session.execute(text(stmt))
    logger.info("Dados de referência carregados.")


async def seed_localizacoes(session) -> None:
    """Cria localizações de estoque (corredor/seção/prateleira) básicas."""
    await session.execute(text("""
        INSERT INTO corredores (nome, descricao) VALUES
            ('A', 'Alimentos'), ('B', 'Bebidas'), ('C', 'Frios')
        ON CONFLICT (nome) DO NOTHING
    """))
    await session.execute(text("""
        INSERT INTO seccoes (corredor_id, nome, descricao)
        SELECT id, 'Seção ' || nome, 'Seção principal do corredor ' || nome
        FROM corredores
        ON CONFLICT (corredor_id, nome) DO NOTHING
    """))
    await session.execute(text("""
        INSERT INTO prateleiras (seccao_id, nome, nivel)
        SELECT id, 'Prateleira 1', 1 FROM seccoes
        ON CONFLICT (seccao_id, nome) DO NOTHING
    """))
    await session.execute(text("""
        INSERT INTO localizacoes_estoque (prateleira_id)
        SELECT id FROM prateleiras
        ON CONFLICT (prateleira_id) DO NOTHING
    """))
    logger.info("Localizações de estoque criadas.")


async def seed_admin(session) -> None:
    """Cria o usuário administrador inicial (se não existir)."""
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@estoque.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    admin_nome = os.environ.get("ADMIN_NOME", "Administrador do Sistema")

    # Cidade padrão (São Paulo - SP, uf = 26)
    row = await session.execute(
        text("SELECT id FROM cidades WHERE uf = 26 ORDER BY id LIMIT 1")
    )
    cidade = row.scalar()
    if cidade is None:
        row = await session.execute(text("SELECT id FROM cidades ORDER BY id LIMIT 1"))
        cidade = row.scalar()

    # Verifica se o admin já existe
    exists = await session.execute(
        text("SELECT 1 FROM usuarios WHERE email = :email"), {"email": admin_email}
    )
    if exists.scalar():
        logger.info("Usuário admin já existe; pulando.")
        return

    # Cria endereço, contato, funcionário e usuário dentro de uma transação
    endereco = await session.execute(
        text("""
            INSERT INTO enderecos (logradouro, numero, complemento, cep, bairro, cidade_id)
            VALUES ('Rua da Administração', '100', NULL, '01001000', 'Centro', :cidade)
            RETURNING id
        """),
        {"cidade": cidade},
    )
    endereco_id = endereco.scalar()

    contato = await session.execute(
        text("""
            INSERT INTO contatos (codigo_pais, ddd, numero)
            VALUES ('+55', '11', '40000000')
            RETURNING id
        """)
    )
    contato_id = contato.scalar()

    funcionario = await session.execute(
        text("""
            INSERT INTO funcionarios (nome_completo, endereco_id, contato_id, ativo)
            VALUES (:nome, :endereco_id, :contato_id, TRUE)
            RETURNING id
        """),
        {"nome": admin_nome, "endereco_id": endereco_id, "contato_id": contato_id},
    )
    funcionario_id = funcionario.scalar()

    await session.execute(
        text("""
            INSERT INTO usuarios (funcionario_id, email, senha_hash, perfil, ativo)
            VALUES (:funcionario_id, :email, :senha_hash, 'admin', TRUE)
        """),
        {
            "funcionario_id": funcionario_id,
            "email": admin_email,
            "senha_hash": hash_password(admin_password),
        },
    )
    logger.info("Usuário admin criado: %s", admin_email)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db_manager.init()
    async with db_manager.sessionmaker() as session:
        await seed_referencia(session)
        await seed_localizacoes(session)
        await seed_admin(session)
        await session.commit()
    await db_manager.close()
    logger.info("Seed concluído com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())