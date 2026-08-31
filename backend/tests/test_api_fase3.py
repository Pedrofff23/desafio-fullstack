import asyncio
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.exc import DBAPIError

from app.core.database import db_manager
from app.models.transacao import RegistroEntrada


@pytest.mark.asyncio(loop_scope="session")
async def test_autenticacao_e_usuario_atual(
    client: AsyncClient, auth_headers: dict[str, str]
):
    sem_token = await client.get("/api/v1/auth/me")
    assert sem_token.status_code == 401

    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "operador@teste.com"
    assert response.json()["funcionario"]["nome_completo"] == "Usuário Operador"


@pytest.mark.asyncio(loop_scope="session")
async def test_usuario_comum_pode_criar_e_filtrar_usuario(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    payload = {
        "nome": "Maria Integração",
        "email": "MARIA@TESTE.COM",
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988888888"},
        "endereco": {
            "logradouro": "Rua Maria",
            "numero": "20",
            "complemento": None,
            "cep": "02002000",
            "bairro": "Centro",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    assert response.json()["email"] == "maria@teste.com"
    usuario_id = response.json()["id"]

    response = await client.get(
        "/api/v1/usuarios", params={"nome": "Maria"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.put(
        f"/api/v1/usuarios/{usuario_id}",
        json={"nome": "Maria Atualizada"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["funcionario"]["nome_completo"] == "Maria Atualizada"

    payload["email"] = "outra@teste.com"
    payload["contato"]["numero"] = "977777777"
    payload["endereco"]["estado_id"] = test_database["outro_estado_id"]
    response = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert response.status_code == 400

    response = await client.delete(
        f"/api/v1/usuarios/{usuario_id}", headers=auth_headers
    )
    assert response.status_code == 200
    response = await client.get(
        f"/api/v1/usuarios/{usuario_id}", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_fluxo_completo_de_estoque_e_concorrencia(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    fornecedor = await client.post(
        "/api/v1/transacoes/fornecedores",
        headers=auth_headers,
        json={
            "nome_empresa": "Fornecedor Teste",
            "ativo": True,
            "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "966666666"},
            "endereco": {
                "logradouro": "Rua Fornecedor",
                "numero": "50",
                "complemento": None,
                "cep": "03003000",
                "bairro": "Centro",
                "estado_id": test_database["estado_id"],
                "cidade_id": test_database["cidade_id"],
            },
        },
    )
    assert fornecedor.status_code == 201, fornecedor.text
    fornecedor_id = fornecedor.json()["id"]
    assert fornecedor.json()["contato"]["ddd"] == "11"

    produto_invalido = await client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "codigo": "P-INVALIDO",
            "nome": "Perecível sem validade",
            "preco": 10,
            "perecivel": True,
            "unidade_medida_id": test_database["unidade_id"],
            "categoria_id": test_database["categoria_id"],
            "localizacao_id": test_database["localizacao_id"],
        },
    )
    assert produto_invalido.status_code == 422

    validade = date.today() + timedelta(days=10)
    produto = await client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "codigo": "P-TESTE",
            "nome": "Produto Integração",
            "descricao": "Teste de estoque",
            "preco": 19.9,
            "perecivel": True,
            "unidade_medida_id": test_database["unidade_id"],
            "categoria_id": test_database["categoria_id"],
            "localizacao_id": test_database["localizacao_id"],
            "lote_inicial": {
                "numero_lote": "LOTE-TESTE",
                "data_producao": str(date.today()),
                "data_validade": str(validade),
            },
        },
    )
    assert produto.status_code == 201, produto.text
    produto_id = produto.json()["id"]
    assert produto.json()["preco"] == 19.9
    assert produto.json()["status"] == "zerado"

    lotes = await client.get(
        f"/api/v1/produtos/{produto_id}/lotes", headers=auth_headers
    )
    lote_id = lotes.json()[0]["id"]

    entrada = await client.post(
        "/api/v1/transacoes/entrada",
        headers=auth_headers,
        json={
            "lote_id": lote_id,
            "fornecedor_id": fornecedor_id,
            "quantidade": 10,
            "tipo_entrada": "compra",
            "observacao": "Entrada do teste",
            "preco_custo": 10,
            "preco_sugerido": 19.9,
        },
    )
    assert entrada.status_code == 201, entrada.text
    entrada_id = entrada.json()["id"]

    async def retirar():
        return await client.post(
            "/api/v1/transacoes/saida",
            headers=auth_headers,
            json={
                "entrada_id": entrada_id,
                "quantidade": 7,
                "tipo_saida": "venda",
                "preco_venda": 19.9,
            },
        )

    respostas = await asyncio.gather(retirar(), retirar())
    assert sorted(resposta.status_code for resposta in respostas) == [201, 400]

    estoque = await client.get("/api/v1/transacoes/estoque", headers=auth_headers)
    linha = next(
        item for item in estoque.json()["items"] if item["produto_id"] == produto_id
    )
    assert linha["quantidade"] == 3

    filtrados = await client.get(
        "/api/v1/produtos",
        params={
            "nome": "Integração",
            "status": "validade_proxima",
            "preco_min": 19,
            "preco_max": 20,
        },
        headers=auth_headers,
    )
    assert filtrados.status_code == 200, filtrados.text
    assert filtrados.json()["total"] == 1

    validade_imutavel = await client.put(
        f"/api/v1/produtos/{produto_id}",
        json={"data_validade": str(validade + timedelta(days=1))},
        headers=auth_headers,
    )
    assert validade_imutavel.status_code == 422

    historico = await client.get(
        "/api/v1/transacoes/historico",
        params={"produto_id": produto_id, "quantidade": 7},
        headers=auth_headers,
    )
    assert historico.status_code == 200, historico.text
    assert historico.json()["total"] == 1
    assert historico.json()["items"][0]["tipo_movimento"] == "venda"

    async with db_manager.sessionmaker() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                delete(RegistroEntrada).where(RegistroEntrada.id == entrada_id)
            )
            await session.commit()
        await session.rollback()

    excluido = await client.delete(
        f"/api/v1/produtos/{produto_id}", headers=auth_headers
    )
    assert excluido.status_code == 200
    detalhe = await client.get(
        f"/api/v1/produtos/{produto_id}", headers=auth_headers
    )
    assert detalhe.status_code == 404
