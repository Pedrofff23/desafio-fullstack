"""Seed de dados de demonstração.

Popula o banco com funcionários, usuários, fornecedores, produtos, lotes e
movimentações de estoque — espelhando o arquivo sql_reference/04_dados_exemplo.pgsql,
porém adaptado para asyncpg/SQLAlchemy e utilizando ON CONFLICT para idempotência.

Pré-requisito:
    - O init_db.py já foi executado (unidades, categorias, localizações e admin existem).
    - Os dados geográficos IBGE (paises, estados, cidades) já foram carregados.

Uso (dentro do container backend ou com .venv ativo):
    python -m scripts.seed_demo
"""

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import text

from app.core.database import db_manager
from app.core.security import hash_password

logger = logging.getLogger("estoque.seed_demo")

# Senha padrão para todos os usuários de demonstração
DEMO_PASSWORD = "Demo@12345"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _scalar(session, stmt: str, params: dict | None = None):
    """Executa um statement e retorna o primeiro valor escalar."""
    result = await session.execute(text(stmt), params or {})
    return result.scalar()


def _data_hora(valor: datetime | str) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if valor == "NOW()":
        return datetime.now(UTC)
    return datetime.fromisoformat(valor)


async def _cidade_id(session, ibge: int | None = None, nome: str | None = None) -> int:
    """Retorna o id de uma cidade pelo código IBGE ou pelo nome."""
    if ibge:
        cid = await _scalar(
            session, "SELECT id FROM cidades WHERE ibge = :ibge LIMIT 1", {"ibge": ibge}
        )
    else:
        cid = await _scalar(
            session, "SELECT id FROM cidades WHERE nome = :nome LIMIT 1", {"nome": nome}
        )
    if cid is None:
        cid = await _scalar(session, "SELECT id FROM cidades ORDER BY id LIMIT 1")
    return cid


# ---------------------------------------------------------------------------
# Endereços
# ---------------------------------------------------------------------------


async def seed_enderecos(session) -> list[int]:
    """Insere os 4 endereços base e devolve seus IDs."""
    enderecos_data = [
        # (logradouro, numero, complemento, cep, bairro, ibge, nome_cidade)
        ("SGAN 912", "340", "Conjunto A", "70830000", "Asa Norte", None, "Brasília"),
        ("Rua dos Aimorés", "250", "Casa 4", "30241000", "Savassi", 3106200, None),
        ("Avenida Paulista", "1842", None, "01310000", "Bela Vista", 3550308, None),
        ("Rua das Flores", "741", "Andar 2", "90044000", "Centro", 4314902, None),
    ]

    ids = []
    for (
        logradouro,
        numero,
        complemento,
        cep,
        bairro,
        ibge,
        nome_cidade,
    ) in enderecos_data:
        cidade_id = await _cidade_id(session, ibge=ibge, nome=nome_cidade)
        params = {
            "logradouro": logradouro,
            "numero": numero,
            "complemento": complemento,
            "cep": cep,
            "bairro": bairro,
            "cidade_id": cidade_id,
        }
        eid = await _scalar(
            session,
            """
            SELECT id FROM enderecos
            WHERE logradouro = :logradouro AND numero = :numero
              AND complemento IS NOT DISTINCT FROM :complemento
              AND cep = :cep AND bairro = :bairro AND cidade_id = :cidade_id
            LIMIT 1
        """,
            params,
        )
        if eid is None:
            eid = await _scalar(
                session,
                """
                INSERT INTO enderecos
                    (logradouro, numero, complemento, cep, bairro, cidade_id)
                VALUES
                    (:logradouro, :numero, :complemento, :cep, :bairro, :cidade_id)
                RETURNING id
            """,
                params,
            )
        ids.append(eid)

    logger.info("Endereços: %s", ids)
    return ids


# ---------------------------------------------------------------------------
# Contatos
# ---------------------------------------------------------------------------


async def seed_contatos(session) -> list[int]:
    """Insere os 4 contatos base e devolve seus IDs."""
    contatos_data = [
        ("+55", "61", "32115500"),
        ("+55", "31", "33998877"),
        ("+55", "11", "99887766"),
        ("+55", "51", "34567890"),
    ]

    ids = []
    for codigo_pais, ddd, numero in contatos_data:
        cid = await _scalar(
            session,
            """
            INSERT INTO contatos (codigo_pais, ddd, numero)
            VALUES (:codigo_pais, :ddd, :numero)
            ON CONFLICT (codigo_pais, ddd, numero) DO NOTHING
            RETURNING id
        """,
            {"codigo_pais": codigo_pais, "ddd": ddd, "numero": numero},
        )
        if cid is None:
            cid = await _scalar(
                session,
                """
                SELECT id FROM contatos
                WHERE codigo_pais = :cp AND ddd = :ddd AND numero = :num
            """,
                {"cp": codigo_pais, "ddd": ddd, "num": numero},
            )
        ids.append(cid)

    logger.info("Contatos: %s", ids)
    return ids


# ---------------------------------------------------------------------------
# Funcionários e Usuários
# ---------------------------------------------------------------------------


async def seed_funcionarios_usuarios(
    session, endereco_ids: list[int], contato_ids: list[int]
) -> list[int]:
    """Cria 4 funcionários com seus respectivos usuários."""
    pessoas = [
        (
            "João Silva",
            endereco_ids[0],
            contato_ids[0],
            "joao.silva@mercado.com",
            "admin",
        ),
        (
            "Maria Santos",
            endereco_ids[1],
            contato_ids[1],
            "maria.santos@mercado.com",
            "funcionario",
        ),
        (
            "Pedro Costa",
            endereco_ids[2],
            contato_ids[2],
            "pedro.costa@mercado.com",
            "funcionario",
        ),
        (
            "Ana Oliveira",
            endereco_ids[3],
            contato_ids[3],
            "ana.oliveira@mercado.com",
            "funcionario",
        ),
    ]

    senha_hash = hash_password(DEMO_PASSWORD)
    func_ids = []

    for nome, end_id, cont_id, email, perfil in pessoas:
        exists = await _scalar(
            session, "SELECT id FROM usuarios WHERE email = :email", {"email": email}
        )
        if exists:
            func_id = await _scalar(
                session,
                "SELECT funcionario_id FROM usuarios WHERE email = :email",
                {"email": email},
            )
            func_ids.append(func_id)
            logger.info("Usuário '%s' já existe; pulando.", email)
            continue

        func_id = await _scalar(
            session,
            """
            INSERT INTO funcionarios (nome_completo, endereco_id, contato_id, ativo)
            VALUES (:nome, :end_id, :cont_id, TRUE)
            RETURNING id
        """,
            {"nome": nome, "end_id": end_id, "cont_id": cont_id},
        )

        await session.execute(
            text("""
            INSERT INTO usuarios (funcionario_id, email, senha_hash, perfil, ativo)
            VALUES (:func_id, :email, :senha_hash, :perfil, TRUE)
        """),
            {
                "func_id": func_id,
                "email": email,
                "senha_hash": senha_hash,
                "perfil": perfil,
            },
        )

        func_ids.append(func_id)
        logger.info("Criado funcionário/usuário: %s (%s)", nome, email)

    return func_ids


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------


async def seed_fornecedores(
    session, contato_ids: list[int], endereco_ids: list[int]
) -> list[int]:
    fornecedores_data = [
        ("Bebidas São Paulo Ltda", contato_ids[2], endereco_ids[2]),
        ("Laticínios Mineiros S.A.", contato_ids[1], endereco_ids[1]),
        ("Frigorífico Sul Carnes Ltda", contato_ids[3], endereco_ids[3]),
        ("Hortifrúti Fresh Delivery", contato_ids[0], endereco_ids[0]),
    ]

    ids = []
    for nome_empresa, cont_id, end_id in fornecedores_data:
        fid = await _scalar(
            session,
            """
            INSERT INTO fornecedores (nome_empresa, contato_id, endereco_id, ativo)
            VALUES (:nome, :cont_id, :end_id, TRUE)
            ON CONFLICT (nome_empresa) DO NOTHING
            RETURNING id
        """,
            {"nome": nome_empresa, "cont_id": cont_id, "end_id": end_id},
        )
        if fid is None:
            fid = await _scalar(
                session,
                "SELECT id FROM fornecedores WHERE nome_empresa = :nome",
                {"nome": nome_empresa},
            )
        ids.append(fid)
        logger.info("Fornecedor '%s': id=%s", nome_empresa, fid)

    return ids


# ---------------------------------------------------------------------------
# Helpers de referência
# ---------------------------------------------------------------------------


async def _unidade(session, sigla: str) -> int:
    return await _scalar(
        session, "SELECT id FROM unidades_medida WHERE sigla = :s", {"s": sigla}
    )


async def _categoria(session, nome: str) -> int:
    return await _scalar(
        session, "SELECT id FROM categorias WHERE nome = :n", {"n": nome}
    )


async def _localizacao(session, idx: int) -> int:
    """Retorna a localizacao_estoque pelo índice (1-based) da tabela."""
    return await _scalar(
        session,
        "SELECT id FROM localizacoes_estoque ORDER BY id LIMIT 1 OFFSET :off",
        {"off": idx - 1},
    )


# ---------------------------------------------------------------------------
# Produto helper
# ---------------------------------------------------------------------------


async def _inserir_produto(session, codigo, nome, descricao, um, cat, loc, func_id):
    pid = await _scalar(
        session,
        """
        INSERT INTO produtos (codigo, nome, descricao, unidade_medida_id, categoria_id,
                              localizacao_id, funcionario_id, ativo)
        VALUES (:c, :n, :d, :um, :cat, :loc, :func, TRUE)
        ON CONFLICT (codigo) DO NOTHING
        RETURNING id
    """,
        {
            "c": codigo,
            "n": nome,
            "d": descricao,
            "um": um,
            "cat": cat,
            "loc": loc,
            "func": func_id,
        },
    )
    if pid is None:
        pid = await _scalar(
            session, "SELECT id FROM produtos WHERE codigo = :c", {"c": codigo}
        )
    return pid


async def _inserir_lote(session, prod_id, numero_lote, dt_prod, dt_val):
    lid = await _scalar(
        session,
        """
        INSERT INTO lotes (produto_id, numero_lote, data_producao, data_validade, ativo)
        VALUES (:pid, :num, :dp, :dv, TRUE)
        ON CONFLICT (produto_id, numero_lote) DO NOTHING
        RETURNING id
    """,
        {"pid": prod_id, "num": numero_lote, "dp": dt_prod, "dv": dt_val},
    )
    if lid is None:
        lid = await _scalar(
            session,
            """
            SELECT id FROM lotes WHERE produto_id = :pid AND numero_lote = :num
        """,
            {"pid": prod_id, "num": numero_lote},
        )
    return lid


async def _inserir_entrada(
    session, lote_id, fornec_id, loc_id, qtd, dt_entrada, p_custo, p_sug, func_id
):
    dt_entrada = _data_hora(dt_entrada)
    eid = await _scalar(
        session,
        "SELECT id FROM registros_entrada WHERE lote_id = :lid LIMIT 1",
        {"lid": lote_id},
    )
    if eid is None:
        eid = await _scalar(
            session,
            """
            INSERT INTO registros_entrada
                (lote_id, fornecedor_id, localizacao_id, quantidade, data_entrada,
                 preco_custo, preco_sugerido, funcionario_id)
            VALUES (:lote_id, :forn_id, :loc_id, :qtd, :dt, :pc, :ps, :func_id)
            RETURNING id
        """,
            {
                "lote_id": lote_id,
                "forn_id": fornec_id,
                "loc_id": loc_id,
                "qtd": qtd,
                "dt": dt_entrada,
                "pc": p_custo,
                "ps": p_sug,
                "func_id": func_id,
            },
        )
    return eid


async def _inserir_saida(session, entrada_id, qtd, dt_saida, p_venda, func_id):
    dt_saida = _data_hora(dt_saida)
    existe = await _scalar(
        session,
        """
        SELECT 1 FROM registros_saida WHERE entrada_id = :eid AND data_saida = :dt
    """,
        {"eid": entrada_id, "dt": dt_saida},
    )
    if not existe:
        await session.execute(
            text("""
            INSERT INTO registros_saida (entrada_id, quantidade, data_saida, preco_venda, funcionario_id)
            VALUES (:eid, :qtd, :dt, :pv, :fid)
        """),
            {
                "eid": entrada_id,
                "qtd": qtd,
                "dt": dt_saida,
                "pv": p_venda,
                "fid": func_id,
            },
        )


# ---------------------------------------------------------------------------
# Produtos completos
# ---------------------------------------------------------------------------


async def seed_produtos(session, func_ids: list[int], fornec_ids: list[int]) -> None:
    """Insere todos os produtos, lotes e movimentações do 04_dados_exemplo.pgsql."""

    # Carrega IDs de referência
    u = {s: await _unidade(session, s) for s in ("l", "un", "kg", "cx", "fr", "pct")}
    c = {
        n: await _categoria(session, n)
        for n in (
            "Laticínios",
            "Bebidas",
            "Carnes",
            "Hortifrúti",
            "Padaria",
            "Bebidas Alcoólicas",
            "Enlatados",
            "Congelados",
            "Doces",
            "Limpeza",
        )
    }
    locs = {i: await _localizacao(session, i) for i in range(1, 7)}

    # Índices de fornecedores: 0=Bebidas SP, 1=Laticinios MG, 2=Frigorifico Sul, 3=Hortifruti
    f = fornec_ids  # alias curto
    fn = func_ids  # alias curto

    # ------------------------------------------------------------------
    # PROD001–PROD008
    # ------------------------------------------------------------------
    p = {}  # prod_ids
    l = {}  # lote_ids
    e = {}  # entrada_ids

    dados = [
        # (codigo, nome, descricao, un, cat, loc_idx, func_idx)
        (
            "PROD001",
            "Leite Integral",
            "Leite de vaca integral pasteurizado 1L",
            "l",
            "Laticínios",
            4,
            0,
        ),
        (
            "PROD002",
            "Iogurte Natural",
            "Iogurte natural sem sabor 500g",
            "un",
            "Laticínios",
            5,
            1,
        ),
        (
            "PROD003",
            "Refrigerante de Cola 2L",
            "Refrigerante de cola 2 litros",
            "l",
            "Bebidas",
            1,
            2,
        ),
        ("PROD004", "Pão Francês", "Pão francês fresco unidade", "un", "Padaria", 6, 3),
        (
            "PROD005",
            "Carne Bovina",
            "Carne bovina alcatra congelada por kg",
            "kg",
            "Carnes",
            2,
            1,
        ),
        (
            "PROD006",
            "Leite sem Lactose",
            "Leite sem lactose 1L",
            "l",
            "Laticínios",
            4,
            2,
        ),
        (
            "PROD007",
            "Ovo de Galinha",
            "Ovos de galinha caipira caixa 12 unidades",
            "cx",
            "Hortifrúti",
            2,
            3,
        ),
        (
            "PROD008",
            "Cerveja Pilsen 6pk",
            "Cerveja Pilsen 6 pack 330ml cada",
            "pct",
            "Bebidas Alcoólicas",
            3,
            0,
        ),
    ]
    for cod, nome, desc, un_s, cat_n, loc_i, f_i in dados:
        p[cod] = await _inserir_produto(
            session, cod, nome, desc, u[un_s], c[cat_n], locs[loc_i], fn[f_i]
        )

    lotes_base = [
        ("LOTE2024001A", "PROD001", date(2024, 1, 10), date(2024, 4, 10)),
        ("LOTE2024001B", "PROD002", date(2024, 1, 15), date(2024, 4, 15)),
        ("LOTE2024002A", "PROD003", date(2024, 2, 1), date(2024, 5, 1)),
        ("LOTE2024003A", "PROD004", date(2024, 3, 5), date(2024, 6, 5)),
        ("LOTE2024004B", "PROD005", date(2024, 2, 15), date(2024, 5, 15)),
        ("LOTENEAR30DIAS", "PROD006", date(2024, 2, 20), date(2024, 3, 20)),
        ("LOTE2024003B", "PROD007", date(2024, 3, 10), date(2024, 6, 10)),
        ("LOTE2024005A", "PROD008", date(2024, 3, 15), date(2024, 6, 15)),
    ]
    for num, prod_cod, dp, dv in lotes_base:
        l[num] = await _inserir_lote(session, p[prod_cod], num, dp, dv)

    async def loc_do_lote(num):
        return await _scalar(
            session,
            """
            SELECT p.localizacao_id FROM lotes l2
            JOIN produtos p ON p.id = l2.produto_id
            WHERE l2.id = :lid
        """,
            {"lid": l[num]},
        )

    entradas_base = [
        # (lote, forn_idx, qtd, dt, p_custo, p_sug, func_idx)
        ("LOTE2024001A", 1, 50, "2024-01-15 09:00:00-03", 3.50, 5.90, 0),
        ("LOTE2024001B", 1, 80, "2024-01-20 10:30:00-03", 2.80, 4.90, 1),
        ("LOTE2024002A", 0, 120, "2024-02-05 14:00:00-03", 7.50, 12.90, 2),
        ("LOTE2024004B", 2, 50, "2024-02-18 11:00:00-03", 18.90, 32.90, 1),
        ("LOTENEAR30DIAS", 1, 20, "2024-02-20 09:00:00-03", 4.20, 7.50, 2),
        ("LOTE2024005A", 0, 60, "2024-02-25 16:00:00-03", 12.00, 22.90, 0),
        ("LOTE2024003A", 3, 200, "2024-03-12 06:00:00-03", 0.45, 1.20, 3),
        ("LOTE2024003B", 3, 40, "2024-03-10 07:00:00-03", 6.00, 11.90, 3),
    ]
    for num, fi, qtd, dt, pc, ps, fni in entradas_base:
        e[num] = await _inserir_entrada(
            session, l[num], f[fi], await loc_do_lote(num), qtd, dt, pc, ps, fn[fni]
        )

    saidas_base = [
        ("LOTE2024001A", 15, "2024-01-20 14:30:00-03", 5.90, 1),
        ("LOTE2024001A", 20, "2024-02-10 09:15:00-03", 5.90, 2),
        ("LOTE2024001B", 30, "2024-01-25 11:00:00-03", 4.90, 1),
        ("LOTE2024002A", 50, "2024-02-15 16:45:00-03", 12.90, 0),
        ("LOTE2024002A", 30, "2024-02-28 10:20:00-03", 12.90, 3),
        ("LOTE2024004B", 12, "2024-02-25 13:00:00-03", 32.90, 1),
        ("LOTE2024004B", 15, "2024-03-05 15:30:00-03", 32.90, 2),
        ("LOTENEAR30DIAS", 8, "2024-02-25 08:00:00-03", 7.50, 3),
        ("LOTENEAR30DIAS", 10, "2024-03-10 11:45:00-03", 7.50, 0),
        ("LOTE2024005A", 25, "2024-03-15 19:00:00-03", 22.90, 3),
        ("LOTE2024003A", 150, "2024-03-13 07:30:00-03", 1.20, 3),
        ("LOTE2024003A", 40, "2024-03-14 08:00:00-03", 1.20, 0),
        ("LOTE2024003B", 20, "2024-03-11 08:30:00-03", 11.90, 0),
        ("LOTE2024003B", 15, "2024-03-12 09:15:00-03", 11.90, 3),
    ]
    for num, qtd, dt, pv, fni in saidas_base:
        await _inserir_saida(session, e[num], qtd, dt, pv, fn[fni])

    logger.info("PROD001–PROD008 inseridos.")

    # ------------------------------------------------------------------
    # PROD009–PROD018
    # ------------------------------------------------------------------
    dados_extra = [
        (
            "PROD009",
            "Arroz Branco 5kg",
            "Arroz branco tipo 1, pacote de 5 kg",
            "pct",
            "Enlatados",
            2,
            0,
        ),
        (
            "PROD010",
            "Feijão Carioca 1kg",
            "Feijão carioca selecionado, pacote de 1 kg",
            "pct",
            "Enlatados",
            2,
            0,
        ),
        (
            "PROD011",
            "Milho Verde em Conserva",
            "Lata de milho verde 170 g",
            "un",
            "Enlatados",
            2,
            1,
        ),
        (
            "PROD012",
            "Batata Frita Congelada",
            "Batata palito congelada, pacote de 1,5 kg",
            "pct",
            "Congelados",
            5,
            1,
        ),
        (
            "PROD013",
            "Sorvete de Chocolate",
            "Sorvete de chocolate, pote de 1,5 L",
            "un",
            "Congelados",
            5,
            2,
        ),
        (
            "PROD014",
            "Banana Prata",
            "Banana prata vendida por quilograma",
            "kg",
            "Hortifrúti",
            6,
            2,
        ),
        (
            "PROD015",
            "Maçã Gala",
            "Maçã gala vendida por quilograma",
            "kg",
            "Hortifrúti",
            6,
            2,
        ),
        (
            "PROD016",
            "Chocolate ao Leite",
            "Barra de chocolate ao leite 90 g",
            "un",
            "Doces",
            2,
            3,
        ),
        (
            "PROD017",
            "Biscoito Recheado",
            "Biscoito recheado sabor chocolate 140 g",
            "pct",
            "Doces",
            2,
            3,
        ),
        (
            "PROD018",
            "Água Sanitária 1L",
            "Água sanitária para limpeza doméstica, 1 L",
            "fr",
            "Limpeza",
            6,
            3,
        ),
    ]
    for cod, nome, desc, un_s, cat_n, loc_i, f_i in dados_extra:
        p[cod] = await _inserir_produto(
            session, cod, nome, desc, u[un_s], c[cat_n], locs[loc_i], fn[f_i]
        )

    lotes_extra = [
        ("LOTE2024006A", "PROD009", date(2024, 2, 10), date(2025, 2, 10)),
        ("LOTE2024006B", "PROD010", date(2024, 2, 12), date(2025, 2, 12)),
        ("LOTE2024006C", "PROD011", date(2024, 1, 20), date(2026, 1, 20)),
        ("LOTE2024007A", "PROD012", date(2024, 3, 1), date(2025, 3, 1)),
        ("LOTE2024007B", "PROD013", date(2024, 3, 5), date(2025, 3, 5)),
        ("LOTE2024008A", "PROD014", date(2024, 3, 18), date(2024, 4, 5)),
        ("LOTE2024008B", "PROD015", date(2024, 3, 18), date(2024, 4, 15)),
        ("LOTE2024009A", "PROD016", date(2024, 2, 1), date(2025, 2, 1)),
        ("LOTE2024009B", "PROD017", date(2024, 2, 5), date(2025, 2, 5)),
        ("LOTE2024010A", "PROD018", date(2024, 3, 10), date(2025, 3, 10)),
    ]
    for num, prod_cod, dp, dv in lotes_extra:
        l[num] = await _inserir_lote(session, p[prod_cod], num, dp, dv)

    entradas_extra = [
        ("LOTE2024006A", 3, 40, "2024-03-18 09:30:00-03", 18.50, 26.90, 0),
        ("LOTE2024006B", 3, 80, "2024-03-18 09:40:00-03", 5.20, 8.90, 0),
        ("LOTE2024006C", 3, 96, "2024-03-19 10:30:00-03", 2.40, 4.50, 1),
        ("LOTE2024007A", 1, 30, "2024-03-19 10:45:00-03", 14.00, 22.90, 1),
        ("LOTE2024007B", 1, 24, "2024-03-20 11:15:00-03", 16.50, 29.90, 2),
        ("LOTE2024008A", 3, 35, "2024-03-20 11:40:00-03", 3.80, 6.99, 2),
        ("LOTE2024008B", 3, 28, "2024-03-20 11:50:00-03", 5.90, 10.99, 2),
        ("LOTE2024009A", 0, 60, "2024-03-21 08:30:00-03", 3.10, 6.50, 3),
        ("LOTE2024009B", 0, 72, "2024-03-21 08:40:00-03", 2.20, 4.90, 3),
        ("LOTE2024010A", 0, 48, "2024-03-21 08:50:00-03", 2.80, 5.50, 3),
    ]
    for num, fi, qtd, dt, pc, ps, fni in entradas_extra:
        e[num] = await _inserir_entrada(
            session, l[num], f[fi], await loc_do_lote(num), qtd, dt, pc, ps, fn[fni]
        )

    saidas_extra = [
        ("LOTE2024006A", 12, "2024-03-22 14:00:00-03", 26.90, 0),
        ("LOTE2024006B", 25, "2024-03-22 14:10:00-03", 8.90, 1),
        ("LOTE2024006C", 30, "2024-03-22 14:20:00-03", 4.50, 1),
        ("LOTE2024007A", 8, "2024-03-23 15:00:00-03", 22.90, 2),
        ("LOTE2024007B", 5, "2024-03-23 15:10:00-03", 29.90, 2),
        ("LOTE2024008A", 14, "2024-03-22 09:00:00-03", 6.99, 3),
        ("LOTE2024008B", 10, "2024-03-22 09:10:00-03", 10.99, 3),
        ("LOTE2024009A", 20, "2024-03-24 16:00:00-03", 6.50, 0),
        ("LOTE2024009B", 18, "2024-03-24 16:10:00-03", 4.90, 0),
        ("LOTE2024010A", 15, "2024-03-24 16:20:00-03", 5.50, 0),
    ]
    for num, qtd, dt, pv, fni in saidas_extra:
        await _inserir_saida(session, e[num], qtd, dt, pv, fn[fni])

    logger.info("PROD009–PROD018 inseridos.")

    # ------------------------------------------------------------------
    # PROD019–PROD022 — validade dinâmica (relativa à data atual)
    # para demonstrar os alertas visuais de vencimento próximo
    # ------------------------------------------------------------------
    hoje = date.today()

    dados_dinamicos = [
        (
            "PROD019",
            "Queijo Muçarela Fatiado",
            "Queijo muçarela fatiado, embalagem de 200 g",
            "pct",
            "Laticínios",
            4,
            0,
        ),
        (
            "PROD020",
            "Iogurte de Morango",
            "Iogurte sabor morango, pote de 170 g",
            "un",
            "Laticínios",
            5,
            1,
        ),
        (
            "PROD021",
            "Peito de Frango Congelado",
            "Peito de frango congelado, pacote de 1 kg",
            "kg",
            "Congelados",
            5,
            2,
        ),
        (
            "PROD022",
            "Suco de Laranja Integral",
            "Suco de laranja integral, garrafa de 1 L",
            "l",
            "Bebidas",
            1,
            3,
        ),
    ]
    for cod, nome, desc, un_s, cat_n, loc_i, f_i in dados_dinamicos:
        p[cod] = await _inserir_produto(
            session, cod, nome, desc, u[un_s], c[cat_n], locs[loc_i], fn[f_i]
        )

    lotes_dinamicos = [
        # (numero_lote, prod_cod, dias_producao, dias_validade, forn_idx, qtd, pc, ps, func_idx, qtd_saida, pv)
        ("LOTE-DEMO-05-DIAS", "PROD019", 20, 5, 1, 30, 8.50, 14.90, 0, 6, 14.90),
        ("LOTE-DEMO-12-DIAS", "PROD020", 10, 12, 1, 48, 2.20, 4.50, 1, 10, 4.50),
        ("LOTE-DEMO-20-DIAS", "PROD021", 15, 20, 2, 25, 17.80, 29.90, 2, 4, 29.90),
        ("LOTE-DEMO-28-DIAS", "PROD022", 7, 28, 0, 36, 5.40, 9.90, 3, 8, 9.90),
    ]

    for (
        num,
        prod_cod,
        dias_p,
        dias_v,
        fi,
        qtd_ent,
        pc,
        ps,
        fni,
        qtd_sai,
        pv,
    ) in lotes_dinamicos:
        dp = hoje - timedelta(days=dias_p)
        dv = hoje + timedelta(days=dias_v)
        l[num] = await _inserir_lote(session, p[prod_cod], num, dp, dv)
        loc_id = await loc_do_lote(num)
        e[num] = await _inserir_entrada(
            session, l[num], f[fi], loc_id, qtd_ent, "NOW()", pc, ps, fn[fni]
        )

        existe = await _scalar(
            session,
            "SELECT 1 FROM registros_saida WHERE entrada_id = :eid LIMIT 1",
            {"eid": e[num]},
        )
        if not existe:
            await session.execute(
                text("""
                INSERT INTO registros_saida (entrada_id, quantidade, data_saida, preco_venda, funcionario_id)
                VALUES (:eid, :qtd, NOW(), :pv, :fid)
            """),
                {"eid": e[num], "qtd": qtd_sai, "pv": pv, "fid": fn[fni]},
            )

    logger.info("PROD019–PROD022 (validade dinâmica) inseridos.")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    db_manager.init()

    async with db_manager.sessionmaker() as session:
        logger.info("Iniciando seed de demonstração...")

        endereco_ids = await seed_enderecos(session)
        await session.flush()

        contato_ids = await seed_contatos(session)
        await session.flush()

        func_ids = await seed_funcionarios_usuarios(session, endereco_ids, contato_ids)
        await session.flush()

        fornec_ids = await seed_fornecedores(session, contato_ids, endereco_ids)
        await session.flush()

        await seed_produtos(session, func_ids, fornec_ids)

        # O preço atual pertence ao produto; os valores da entrada ficam como
        # histórico de compra. Os dados demo possuem lotes com validade.
        await session.execute(
            text("""
            UPDATE produtos p
               SET preco = dados.preco,
                   perecivel = TRUE
              FROM (
                    SELECT l.produto_id, MAX(re.preco_sugerido) AS preco
                      FROM lotes l
                      JOIN registros_entrada re ON re.lote_id = l.id
                     GROUP BY l.produto_id
                   ) dados
             WHERE p.id = dados.produto_id
        """)
        )

        await session.commit()

    await db_manager.close()
    logger.info("Seed de demonstração concluído com sucesso.")
    logger.info("Credenciais dos usuários demo (senha: %s):", DEMO_PASSWORD)
    logger.info("  joao.silva@mercado.com  (admin)")
    logger.info("  maria.santos@mercado.com")
    logger.info("  pedro.costa@mercado.com")
    logger.info("  ana.oliveira@mercado.com")


if __name__ == "__main__":
    asyncio.run(main())
