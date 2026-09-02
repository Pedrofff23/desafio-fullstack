import asyncio
import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.core.config import settings
from app.core.database import db_manager
from app.core.security import hash_password
from app.models.localidade import Cidade, Contato, Endereco, Estado, Pais
from app.models.produto import (
    Categoria,
    Corredor,
    LocalizacaoEstoque,
    Prateleira,
    Seccao,
    UnidadeMedida,
)
from app.models.usuario import Funcionario, Usuario

TEST_DATABASE_NAME = "gerenciamento_estoque_test"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_database() -> AsyncGenerator[dict, None]:
    original_url = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    parsed = make_url(original_url)
    admin_url = parsed.set(database="postgres").render_as_string(hide_password=False)
    test_url = parsed.set(database=TEST_DATABASE_NAME).render_as_string(
        hide_password=False
    )

    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(
            text(f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}" WITH (FORCE)')
        )
        await conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    await admin_engine.dispose()

    settings.DATABASE_URL = test_url
    cfg = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    db_manager.init()

    async with db_manager.sessionmaker() as session:
        pais = Pais(nome="Brasil", nome_pt="Brasil", sigla="BR")
        estado = Estado(nome="São Paulo", uf="SP", ibge=35, pais_rel=pais)
        outro_estado = Estado(nome="Rio de Janeiro", uf="RJ", ibge=33, pais_rel=pais)
        cidade = Cidade(nome="São Paulo", ibge=3550308, estado=estado)
        outra_cidade = Cidade(nome="Rio de Janeiro", ibge=3304557, estado=outro_estado)

        unidade = UnidadeMedida(sigla="un", descricao="Unidade")
        categoria = Categoria(nome="Alimentos", descricao="Produtos alimentícios")
        corredor = Corredor(nome="A", descricao="Principal")
        seccao = Seccao(nome="Seção A", descricao="Principal")
        session.add_all(
            [
                pais,
                estado,
                outro_estado,
                cidade,
                outra_cidade,
                unidade,
                categoria,
                corredor,
            ]
        )
        await session.flush()

        if seccao.id is None:
            seccao.corredor_id = corredor.id
            session.add(seccao)
            await session.flush()
        prateleira = Prateleira(seccao_id=seccao.id, nome="Prateleira 1", nivel=1)
        session.add(prateleira)
        await session.flush()
        localizacao = LocalizacaoEstoque(prateleira_id=prateleira.id)

        endereco = Endereco(
            logradouro="Rua Teste",
            numero="1",
            cep="01001000",
            bairro="Centro",
            cidade=cidade,
        )
        contato = Contato(codigo_pais="+55", ddd="11", numero="999999999")
        funcionario = Funcionario(
            nome_completo="Usuário Operador",
            endereco=endereco,
            contato=contato,
            ativo=True,
        )
        usuario = Usuario(
            funcionario=funcionario,
            email="operador@teste.com",
            senha_hash=hash_password("Senha123"),
            perfil="funcionario",
            ativo=True,
        )
        session.add_all([localizacao, usuario])
        await session.commit()

        dados = {
            "estado_id": estado.id,
            "outro_estado_id": outro_estado.id,
            "cidade_id": cidade.id,
            "unidade_id": unidade.id,
            "categoria_id": categoria.id,
            "localizacao_id": localizacao.id,
        }

    yield dados

    await db_manager.close()
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(
            text(f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}" WITH (FORCE)')
        )
    await admin_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client(test_database) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        yield http_client


@pytest_asyncio.fixture(scope="session")
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "operador@teste.com", "senha": "Senha123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
