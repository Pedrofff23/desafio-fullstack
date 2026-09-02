"""criar schema inicial

Revision ID: 3c3c56834314
Revises:
Create Date: 2026-08-28 17:10:52.962043

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c3c56834314"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ===== Tabelas independentes =====
    op.create_table(
        "alergenos",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "categorias",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "contatos",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("codigo_pais", sa.String(length=4), nullable=False),
        sa.Column("ddd", sa.String(length=2), nullable=False),
        sa.Column("numero", sa.String(length=15), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo_pais", "ddd", "numero"),
    )
    op.create_table(
        "corredores",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "ingredientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "paises",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(length=60), nullable=True),
        sa.Column("nome_pt", sa.String(length=60), nullable=True),
        sa.Column("sigla", sa.String(length=2), nullable=True),
        sa.Column("bacen", sa.Integer(), nullable=True),
        sa.Column("ddi", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "unidades_medida",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("sigla", sa.String(length=10), nullable=False),
        sa.Column("descricao", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("descricao"),
        sa.UniqueConstraint("sigla"),
    )

    # ===== Hierarquia geográfica: estados -> cidades -> enderecos =====
    op.create_table(
        "estados",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(length=60), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("ibge", sa.Integer(), nullable=True),
        sa.Column("pais", sa.BigInteger(), nullable=True),
        sa.Column("ddd", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["pais"],
            ["paises.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cidades",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=True),
        sa.Column("uf", sa.BigInteger(), nullable=True),
        sa.Column("ibge", sa.Integer(), nullable=True),
        sa.Column("lat_lon", sa.Text(), nullable=True),
        sa.Column("cod_tom", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["uf"],
            ["estados.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "enderecos",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("logradouro", sa.String(length=150), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("complemento", sa.String(length=100), nullable=True),
        sa.Column("cep", sa.String(length=8), nullable=False),
        sa.Column("bairro", sa.String(length=100), nullable=False),
        sa.Column("cidade_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cidade_id"],
            ["cidades.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "logradouro", "numero", "complemento", "cep", "bairro", "cidade_id"
        ),
    )

    # ===== Hierarquia de localização: corredores -> seccoes -> prateleiras -> localizacoes =====
    op.create_table(
        "seccoes",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("corredor_id", sa.SmallInteger(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["corredor_id"],
            ["corredores.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("corredor_id", "nome"),
    )
    op.create_table(
        "prateleiras",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("seccao_id", sa.SmallInteger(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("nivel", sa.SmallInteger(), nullable=True),
        sa.Column("descricao", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["seccao_id"],
            ["seccoes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seccao_id", "nome"),
    )
    op.create_table(
        "localizacoes_estoque",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("prateleira_id", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prateleira_id"],
            ["prateleiras.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prateleira_id"),
    )

    # ===== Pessoas e autenticação (funcionarios antes de usuarios) =====
    # funcionarios.excluido_por é adicionado ao final (FK circular com usuarios).
    op.create_table(
        "funcionarios",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nome_completo", sa.String(length=150), nullable=False),
        sa.Column("endereco_id", sa.BigInteger(), nullable=False),
        sa.Column("contato_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excluido_por", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["contato_id"],
            ["contatos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["endereco_id"],
            ["enderecos.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "usuarios",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("funcionario_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("perfil", sa.String(length=20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excluido_por", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["excluido_por"],
            ["usuarios.id"],
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_id"],
            ["funcionarios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("funcionario_id"),
    )
    op.create_table(
        "sessoes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "data_criacao",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("data_expiracao", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ativa", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    # FK circular: funcionarios.excluido_por -> usuarios.id
    op.create_foreign_key(
        "fk_funcionario_excluido_por",
        "funcionarios",
        "usuarios",
        ["excluido_por"],
        ["id"],
    )

    # ===== Fornecedores =====
    op.create_table(
        "fornecedores",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nome_empresa", sa.String(length=150), nullable=False),
        sa.Column("contato_id", sa.BigInteger(), nullable=False),
        sa.Column("endereco_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excluido_por", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["contato_id"],
            ["contatos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["endereco_id"],
            ["enderecos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["excluido_por"],
            ["usuarios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome_empresa"),
    )

    # ===== Produtos e lotes =====
    op.create_table(
        "produtos",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("unidade_medida_id", sa.SmallInteger(), nullable=False),
        sa.Column("categoria_id", sa.SmallInteger(), nullable=False),
        sa.Column("localizacao_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("funcionario_id", sa.BigInteger(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excluido_por", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
        ),
        sa.ForeignKeyConstraint(
            ["excluido_por"],
            ["usuarios.id"],
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_id"],
            ["funcionarios.id"],
        ),
        sa.ForeignKeyConstraint(
            ["localizacao_id"],
            ["localizacoes_estoque.id"],
        ),
        sa.ForeignKeyConstraint(
            ["unidade_medida_id"],
            ["unidades_medida.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_table(
        "lotes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("produto_id", sa.BigInteger(), nullable=False),
        sa.Column("numero_lote", sa.String(length=50), nullable=False),
        sa.Column("data_producao", sa.Date(), nullable=False),
        sa.Column("data_validade", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excluido_por", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["excluido_por"],
            ["usuarios.id"],
        ),
        sa.ForeignKeyConstraint(
            ["produto_id"],
            ["produtos.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("produto_id", "numero_lote"),
    )

    # ===== Movimentações =====
    op.create_table(
        "registros_entrada",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("lote_id", sa.BigInteger(), nullable=False),
        sa.Column("fornecedor_id", sa.BigInteger(), nullable=False),
        sa.Column("localizacao_id", sa.BigInteger(), nullable=False),
        sa.Column("quantidade", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column(
            "data_entrada",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("preco_custo", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("preco_sugerido", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("funcionario_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["fornecedor_id"],
            ["fornecedores.id"],
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_id"],
            ["funcionarios.id"],
        ),
        sa.ForeignKeyConstraint(
            ["localizacao_id"],
            ["localizacoes_estoque.id"],
        ),
        sa.ForeignKeyConstraint(
            ["lote_id"],
            ["lotes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "registros_saida",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("entrada_id", sa.BigInteger(), nullable=False),
        sa.Column("quantidade", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column(
            "data_saida",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("preco_venda", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("funcionario_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entrada_id"],
            ["registros_entrada.id"],
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_id"],
            ["funcionarios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ===== Views de estoque (saldo por entrada e por produto) =====
    op.execute("""
        CREATE VIEW estoque_entrada AS
        SELECT
            e.id AS entrada_id,
            e.lote_id,
            l.produto_id,
            e.fornecedor_id,
            e.localizacao_id,
            e.quantidade - COALESCE(s.quantidade_saida, 0) AS quantidade
        FROM registros_entrada e
            JOIN lotes l ON l.id = e.lote_id
            LEFT JOIN (
                SELECT entrada_id, SUM(quantidade) AS quantidade_saida
                FROM registros_saida
                GROUP BY entrada_id
            ) s ON s.entrada_id = e.id
    """)

    op.execute("""
        CREATE VIEW estoque_produto AS
        SELECT lote_id, produto_id, SUM(quantidade) AS quantidade
        FROM estoque_entrada
        GROUP BY lote_id, produto_id
    """)

    # ===== Trigger: impede saída maior que o saldo da entrada (concorrência) =====
    op.execute("""
        CREATE OR REPLACE FUNCTION validar_saldo_saida()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            AS $$
        DECLARE
            saldo_atual numeric(14, 3);
        BEGIN
            SELECT
                re.quantidade - COALESCE((
                    SELECT SUM(rs.quantidade)
                    FROM registros_saida rs
                    WHERE rs.entrada_id = NEW.entrada_id
                      AND (TG_OP <> 'UPDATE' OR rs.id <> OLD.id)
                ), 0)
            INTO saldo_atual
            FROM registros_entrada re
            WHERE re.id = NEW.entrada_id
            FOR UPDATE;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Entrada % inexistente', NEW.entrada_id;
            END IF;
            IF COALESCE(saldo_atual, 0) < NEW.quantidade THEN
                RAISE EXCEPTION 'Saldo insuficiente para a entrada %', NEW.entrada_id;
            END IF;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        CREATE TRIGGER trg_validar_saldo_saida
            BEFORE INSERT OR UPDATE OF entrada_id, quantidade ON registros_saida
            FOR EACH ROW
            EXECUTE FUNCTION validar_saldo_saida();
    """)

    # ===== Índices de desempenho =====
    op.execute("CREATE INDEX idx_endereco_cidade ON enderecos(cidade_id);")
    op.execute("CREATE INDEX idx_produto_categoria ON produtos(categoria_id);")
    op.execute("CREATE INDEX idx_lote_validade ON lotes(data_validade);")
    op.execute("CREATE INDEX idx_entrada_data ON registros_entrada(data_entrada);")
    op.execute(
        "CREATE INDEX idx_entrada_fornecedor ON registros_entrada(fornecedor_id);"
    )
    op.execute("CREATE INDEX idx_entrada_lote ON registros_entrada(lote_id);")
    op.execute(
        "CREATE INDEX idx_entrada_localizacao ON registros_entrada(localizacao_id);"
    )
    op.execute("CREATE INDEX idx_saida_data ON registros_saida(data_saida);")
    op.execute("CREATE INDEX idx_saida_entrada ON registros_saida(entrada_id);")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_validar_saldo_saida ON registros_saida;")
    op.execute("DROP FUNCTION IF EXISTS validar_saldo_saida();")
    op.execute("DROP VIEW IF EXISTS estoque_produto;")
    op.execute("DROP VIEW IF EXISTS estoque_entrada;")
    op.drop_table("registros_saida")
    op.drop_table("registros_entrada")
    op.drop_table("lotes")
    op.drop_table("produtos")
    op.drop_table("fornecedores")
    op.drop_constraint(
        "fk_funcionario_excluido_por", "funcionarios", type_="foreignkey"
    )
    op.drop_table("sessoes")
    op.drop_table("usuarios")
    op.drop_table("funcionarios")
    op.drop_table("localizacoes_estoque")
    op.drop_table("enderecos")
    op.drop_table("prateleiras")
    op.drop_table("cidades")
    op.drop_table("seccoes")
    op.drop_table("estados")
    op.drop_table("unidades_medida")
    op.drop_table("paises")
    op.drop_table("ingredientes")
    op.drop_table("corredores")
    op.drop_table("contatos")
    op.drop_table("categorias")
    op.drop_table("alergenos")
