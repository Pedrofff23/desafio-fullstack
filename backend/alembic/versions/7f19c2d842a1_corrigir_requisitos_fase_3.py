"""corrigir requisitos da fase 3

Revision ID: 7f19c2d842a1
Revises: 3c3c56834314
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f19c2d842a1"
down_revision: Union[str, None] = "3c3c56834314"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


IDENTITY_SMALLINT = [
    "unidades_medida",
    "categorias",
    "alergenos",
    "corredores",
    "seccoes",
    "prateleiras",
]
IDENTITY_INTEGER = ["ingredientes"]
IDENTITY_BIGINT = [
    "enderecos",
    "contatos",
    "funcionarios",
    "usuarios",
    "fornecedores",
    "localizacoes_estoque",
    "produtos",
    "nutrientes",
    "lotes",
    "registros_entrada",
    "registros_saida",
    "sessoes",
]
IDENTITY_TABLES = IDENTITY_SMALLINT + IDENTITY_INTEGER + IDENTITY_BIGINT

CATALOG_FKS = [
    ("seccoes", "seccoes_corredor_id_fkey", "corredor_id", "corredores"),
    ("prateleiras", "prateleiras_seccao_id_fkey", "seccao_id", "seccoes"),
    (
        "localizacoes_estoque",
        "localizacoes_estoque_prateleira_id_fkey",
        "prateleira_id",
        "prateleiras",
    ),
    (
        "produtos",
        "produtos_unidade_medida_id_fkey",
        "unidade_medida_id",
        "unidades_medida",
    ),
    ("produtos", "produtos_categoria_id_fkey", "categoria_id", "categorias"),
    (
        "produtos_alergenos",
        "produtos_alergenos_alergeno_id_fkey",
        "alergeno_id",
        "alergenos",
    ),
]
GEO_FKS = [
    ("estados", "estados_pais_fkey", "pais", "paises"),
    ("cidades", "cidades_uf_fkey", "uf", "estados"),
    ("enderecos", "enderecos_cidade_id_fkey", "cidade_id", "cidades"),
]


def _drop_foreign_keys(items: list[tuple[str, str, str, str]]) -> None:
    for tabela, nome, _, _ in items:
        op.drop_constraint(nome, tabela, type_="foreignkey")


def _create_foreign_keys(items: list[tuple[str, str, str, str]]) -> None:
    for tabela, nome, coluna, referenciada in items:
        op.create_foreign_key(nome, tabela, referenciada, [coluna], ["id"])


def _serial_to_identity() -> None:
    for tabela in IDENTITY_TABLES:
        op.execute(f"ALTER TABLE {tabela} ALTER COLUMN id DROP DEFAULT")
        op.execute(f"DROP SEQUENCE IF EXISTS {tabela}_id_seq")
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN id "
            "ADD GENERATED ALWAYS AS IDENTITY"
        )
        op.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{tabela}', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM {tabela}
        """)


def _identity_to_serial() -> None:
    tipos = {
        **{tabela: "integer" for tabela in IDENTITY_SMALLINT},
        **{tabela: "integer" for tabela in IDENTITY_INTEGER},
        **{tabela: "bigint" for tabela in IDENTITY_BIGINT},
    }
    for tabela in reversed(IDENTITY_TABLES):
        tipo = tipos[tabela]
        op.execute(f"ALTER TABLE {tabela} ALTER COLUMN id DROP IDENTITY IF EXISTS")
        op.execute(f"CREATE SEQUENCE {tabela}_id_seq AS {tipo}")
        op.execute(f"ALTER SEQUENCE {tabela}_id_seq OWNED BY {tabela}.id")
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN id "
            f"SET DEFAULT nextval('{tabela}_id_seq'::regclass)"
        )
        op.execute(f"""
            SELECT setval(
                '{tabela}_id_seq',
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM {tabela}
        """)


def upgrade() -> None:
    op.add_column(
        "produtos",
        sa.Column("preco", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "produtos",
        sa.Column("perecivel", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("lotes", "data_validade", existing_type=sa.Date(), nullable=True)

    op.add_column(
        "registros_entrada",
        sa.Column("tipo_entrada", sa.String(50), nullable=False, server_default="compra"),
    )
    op.add_column("registros_entrada", sa.Column("observacao", sa.Text()))
    op.add_column(
        "registros_saida",
        sa.Column("tipo_saida", sa.String(50), nullable=False, server_default="venda"),
    )

    op.create_table(
        "nutrientes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            sa.ForeignKey("produtos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(50), nullable=False),
        sa.Column("unidade", sa.String(10), nullable=False),
        sa.Column("valor", sa.Numeric(10, 3), nullable=False),
        sa.CheckConstraint("valor >= 0", name="ck_nutrientes_valor"),
        sa.UniqueConstraint("produto_id", "nome"),
    )
    op.create_table(
        "produtos_ingredientes",
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            sa.ForeignKey("produtos.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "ingrediente_id",
            sa.Integer(),
            sa.ForeignKey("ingredientes.id"),
            primary_key=True,
        ),
        sa.Column("ordem", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("ordem > 0", name="ck_produtos_ingredientes_ordem"),
        sa.UniqueConstraint("produto_id", "ordem"),
    )
    op.create_table(
        "produtos_alergenos",
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            sa.ForeignKey("produtos.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "alergeno_id",
            sa.SmallInteger(),
            sa.ForeignKey("alergenos.id"),
            primary_key=True,
        ),
    )

    checks = [
        ("ck_contatos_codigo_pais", "contatos", "codigo_pais ~ '^\\+[1-9][0-9]{0,2}$'"),
        ("ck_contatos_ddd", "contatos", "ddd ~ '^[0-9]{2}$'"),
        ("ck_contatos_numero", "contatos", "numero ~ '^[0-9]{8,15}$'"),
        ("ck_enderecos_cep", "enderecos", "cep ~ '^[0-9]{8}$'"),
        (
            "ck_usuarios_email",
            "usuarios",
            "email = lower(btrim(email)) AND "
            "email ~ '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$'",
        ),
        ("ck_usuarios_perfil", "usuarios", "perfil IN ('admin', 'funcionario')"),
        ("ck_sessoes_expiracao", "sessoes", "data_expiracao > data_criacao"),
        ("ck_prateleiras_nivel", "prateleiras", "nivel IS NULL OR nivel > 0"),
        ("ck_produtos_preco", "produtos", "preco >= 0"),
        (
            "ck_lotes_validade",
            "lotes",
            "data_validade IS NULL OR data_validade >= data_producao",
        ),
        ("ck_entrada_quantidade", "registros_entrada", "quantidade > 0"),
        ("ck_entrada_preco_custo", "registros_entrada", "preco_custo >= 0"),
        ("ck_entrada_preco_sugerido", "registros_entrada", "preco_sugerido >= 0"),
        ("ck_saida_quantidade", "registros_saida", "quantidade > 0"),
        ("ck_saida_preco_venda", "registros_saida", "preco_venda >= 0"),
    ]
    for nome, tabela, condicao in checks:
        op.create_check_constraint(nome, tabela, condicao)

    op.execute("""
        CREATE OR REPLACE FUNCTION validar_quantidade_entrada()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE quantidade_retirada numeric(14, 3);
        BEGIN
            SELECT COALESCE(SUM(quantidade), 0)
              INTO quantidade_retirada
              FROM registros_saida
             WHERE entrada_id = OLD.id;
            IF NEW.quantidade < quantidade_retirada THEN
                RAISE EXCEPTION
                    'Quantidade da entrada % não pode ser menor que a quantidade já retirada (%)',
                    OLD.id, quantidade_retirada;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_validar_quantidade_entrada
        BEFORE UPDATE OF quantidade ON registros_entrada
        FOR EACH ROW EXECUTE FUNCTION validar_quantidade_entrada()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION impedir_exclusao_movimentacao()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Movimentações de estoque não podem ser excluídas';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_impedir_exclusao_entrada
        BEFORE DELETE ON registros_entrada
        FOR EACH ROW EXECUTE FUNCTION impedir_exclusao_movimentacao()
    """)
    op.execute("""
        CREATE TRIGGER trg_impedir_exclusao_saida
        BEFORE DELETE ON registros_saida
        FOR EACH ROW EXECUTE FUNCTION impedir_exclusao_movimentacao()
    """)

    # Mantém a estrutura do banco anterior usando tipos nativos e CHECKs.
    _drop_foreign_keys(GEO_FKS + CATALOG_FKS)

    op.execute("ALTER TABLE estados ALTER COLUMN pais TYPE integer USING pais::integer")
    op.execute("ALTER TABLE cidades ALTER COLUMN uf TYPE integer USING uf::integer")
    op.execute("ALTER TABLE cidades ALTER COLUMN lat_lon TYPE point USING lat_lon::point")
    op.execute(
        "ALTER TABLE cidades ALTER COLUMN cod_tom TYPE smallint USING cod_tom::smallint"
    )
    op.execute(
        "ALTER TABLE enderecos ALTER COLUMN cidade_id TYPE integer "
        "USING cidade_id::integer"
    )
    for tabela in IDENTITY_SMALLINT:
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN id TYPE smallint USING id::smallint"
        )
    for tabela, _, coluna, _ in CATALOG_FKS:
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN {coluna} TYPE smallint "
            f"USING {coluna}::smallint"
        )

    op.execute("ALTER TABLE contatos DROP CONSTRAINT IF EXISTS ck_contatos_ddd")
    op.execute("ALTER TABLE enderecos DROP CONSTRAINT IF EXISTS ck_enderecos_cep")
    op.execute("ALTER TABLE contatos ALTER COLUMN ddd TYPE char(2) USING ddd::char(2)")
    op.execute("ALTER TABLE enderecos ALTER COLUMN cep TYPE char(8) USING cep::char(8)")
    _create_foreign_keys(GEO_FKS + CATALOG_FKS)

    op.execute("ALTER TABLE contatos ALTER COLUMN codigo_pais SET DEFAULT '+55'")
    op.execute("ALTER TABLE cidades ALTER COLUMN cod_tom SET DEFAULT 0")
    for tabela, coluna in [
        ("funcionarios", "ativo"),
        ("usuarios", "ativo"),
        ("fornecedores", "ativo"),
        ("produtos", "ativo"),
        ("lotes", "ativo"),
        ("sessoes", "ativa"),
    ]:
        op.execute(f"ALTER TABLE {tabela} ALTER COLUMN {coluna} SET DEFAULT TRUE")

    for nome, tabela, condicao in [
        ("ck_unidades_medida_sigla", "unidades_medida", "sigla = lower(btrim(sigla))"),
        ("ck_produtos_codigo_formato", "produtos", "codigo = btrim(codigo) AND codigo <> ''"),
        ("ck_lotes_numero_lote_formato", "lotes", "numero_lote = btrim(numero_lote) AND numero_lote <> ''"),
        ("ck_funcionarios_nome_formato", "funcionarios", "nome_completo = btrim(nome_completo) AND nome_completo <> ''"),
        ("ck_fornecedores_nome_formato", "fornecedores", "nome_empresa = btrim(nome_empresa) AND nome_empresa <> ''"),
        ("ck_produtos_nome_formato", "produtos", "nome = btrim(nome) AND nome <> ''"),
        ("ck_usuarios_senha_hash_tamanho", "usuarios", "length(senha_hash) >= 20"),
        ("ck_contatos_ddd", "contatos", "ddd ~ '^[0-9]{2}$'"),
        ("ck_enderecos_cep", "enderecos", "cep ~ '^[0-9]{8}$'"),
    ]:
        op.create_check_constraint(nome, tabela, condicao)

    op.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_email")
    op.create_check_constraint(
        "ck_usuarios_email",
        "usuarios",
        "email = lower(btrim(email)) AND "
        "email ~ '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$'",
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION preencher_localizacao_entrada()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.localizacao_id IS NULL THEN
                SELECT p.localizacao_id INTO NEW.localizacao_id
                FROM lotes l JOIN produtos p ON p.id = l.produto_id
                WHERE l.id = NEW.lote_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_preencher_localizacao_entrada
        BEFORE INSERT OR UPDATE OF lote_id ON registros_entrada
        FOR EACH ROW EXECUTE FUNCTION preencher_localizacao_entrada()
    """)
    _serial_to_identity()


def downgrade() -> None:
    _identity_to_serial()
    op.execute(
        "DROP TRIGGER IF EXISTS trg_preencher_localizacao_entrada "
        "ON registros_entrada"
    )
    op.execute("DROP FUNCTION IF EXISTS preencher_localizacao_entrada()")
    for tabela, constraint in [
        ("unidades_medida", "ck_unidades_medida_sigla"),
        ("produtos", "ck_produtos_codigo_formato"),
        ("lotes", "ck_lotes_numero_lote_formato"),
        ("funcionarios", "ck_funcionarios_nome_formato"),
        ("fornecedores", "ck_fornecedores_nome_formato"),
        ("produtos", "ck_produtos_nome_formato"),
        ("usuarios", "ck_usuarios_senha_hash_tamanho"),
    ]:
        op.drop_constraint(constraint, tabela, type_="check")
    op.execute("ALTER TABLE contatos ALTER COLUMN codigo_pais DROP DEFAULT")
    op.execute("ALTER TABLE cidades ALTER COLUMN cod_tom DROP DEFAULT")
    for tabela, coluna in [
        ("funcionarios", "ativo"),
        ("usuarios", "ativo"),
        ("fornecedores", "ativo"),
        ("produtos", "ativo"),
        ("lotes", "ativo"),
        ("sessoes", "ativa"),
    ]:
        op.execute(f"ALTER TABLE {tabela} ALTER COLUMN {coluna} DROP DEFAULT")

    _drop_foreign_keys(GEO_FKS + CATALOG_FKS)
    op.execute("ALTER TABLE contatos DROP CONSTRAINT ck_contatos_ddd")
    op.execute("ALTER TABLE enderecos DROP CONSTRAINT ck_enderecos_cep")
    op.execute(
        "ALTER TABLE contatos ALTER COLUMN ddd TYPE varchar(2) USING ddd::varchar(2)"
    )
    op.execute(
        "ALTER TABLE enderecos ALTER COLUMN cep TYPE varchar(8) USING cep::varchar(8)"
    )
    op.create_check_constraint("ck_contatos_ddd", "contatos", "ddd ~ '^[0-9]{2}$'")
    op.create_check_constraint("ck_enderecos_cep", "enderecos", "cep ~ '^[0-9]{8}$'")
    for tabela, _, coluna, _ in reversed(CATALOG_FKS):
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN {coluna} TYPE integer "
            f"USING {coluna}::integer"
        )
    for tabela in reversed(IDENTITY_SMALLINT):
        op.execute(
            f"ALTER TABLE {tabela} ALTER COLUMN id TYPE integer USING id::integer"
        )
    op.execute(
        "ALTER TABLE enderecos ALTER COLUMN cidade_id TYPE bigint "
        "USING cidade_id::bigint"
    )
    op.execute(
        "ALTER TABLE cidades ALTER COLUMN cod_tom TYPE integer USING cod_tom::integer"
    )
    op.execute(
        "ALTER TABLE cidades ALTER COLUMN lat_lon TYPE text USING lat_lon::text"
    )
    op.execute("ALTER TABLE cidades ALTER COLUMN uf TYPE bigint USING uf::bigint")
    op.execute("ALTER TABLE estados ALTER COLUMN pais TYPE bigint USING pais::bigint")
    _create_foreign_keys(GEO_FKS + CATALOG_FKS)

    op.execute("DROP TRIGGER IF EXISTS trg_impedir_exclusao_saida ON registros_saida")
    op.execute("DROP TRIGGER IF EXISTS trg_impedir_exclusao_entrada ON registros_entrada")
    op.execute("DROP FUNCTION IF EXISTS impedir_exclusao_movimentacao()")
    op.execute("DROP TRIGGER IF EXISTS trg_validar_quantidade_entrada ON registros_entrada")
    op.execute("DROP FUNCTION IF EXISTS validar_quantidade_entrada()")

    checks = [
        ("ck_saida_preco_venda", "registros_saida"),
        ("ck_saida_quantidade", "registros_saida"),
        ("ck_entrada_preco_sugerido", "registros_entrada"),
        ("ck_entrada_preco_custo", "registros_entrada"),
        ("ck_entrada_quantidade", "registros_entrada"),
        ("ck_lotes_validade", "lotes"),
        ("ck_produtos_preco", "produtos"),
        ("ck_prateleiras_nivel", "prateleiras"),
        ("ck_sessoes_expiracao", "sessoes"),
        ("ck_usuarios_perfil", "usuarios"),
        ("ck_usuarios_email", "usuarios"),
        ("ck_enderecos_cep", "enderecos"),
        ("ck_contatos_numero", "contatos"),
        ("ck_contatos_ddd", "contatos"),
        ("ck_contatos_codigo_pais", "contatos"),
    ]
    for nome, tabela in checks:
        op.drop_constraint(nome, tabela, type_="check")

    op.drop_table("produtos_alergenos")
    op.drop_table("produtos_ingredientes")
    op.drop_table("nutrientes")
    op.drop_column("registros_saida", "tipo_saida")
    op.drop_column("registros_entrada", "observacao")
    op.drop_column("registros_entrada", "tipo_entrada")
    op.alter_column("lotes", "data_validade", existing_type=sa.Date(), nullable=False)
    op.drop_column("produtos", "perecivel")
    op.drop_column("produtos", "preco")
