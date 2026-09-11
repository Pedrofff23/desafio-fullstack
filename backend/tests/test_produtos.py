from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_catalogo_produtos_retorna_dados_necessarios(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa endpoint de catálogo com categorias, unidades, alérgenos, etc."""
    response = await client.get("/api/v1/produtos/catalogo", headers=auth_headers)
    assert response.status_code == 200, response.text
    catalogo = response.json()
    assert "categorias" in catalogo
    assert "unidades_medida" in catalogo
    assert "localizacoes" in catalogo
    assert "ingredientes" in catalogo
    assert "alergenos" in catalogo


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_produto_perecivel_sem_validade_retorna_422(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Regra de negócio: Produto perecível com lote inicial exige data de validade."""
    payload = {
        "codigo": "P-PERECIVEL-SEM-VALIDADE",
        "nome": "Iogurte Natural",
        "preco": 5.50,
        "perecivel": True,
        "unidade_medida_id": test_database["unidade_id"],
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
        "lote_inicial": {
            "numero_lote": "LOTE-SEM-VAL",
            "data_producao": str(date.today()),
            "data_validade": None,
        },
    }
    response = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_produto_perecivel_sem_lote_inicial_sucesso(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Regra de negócio: Produto perecível pode ser cadastrado sem lote inicial."""
    payload = {
        "codigo": "P-PERECIVEL-SEM-LOTE",
        "nome": "Iogurte Natural Sem Lote",
        "preco": 5.50,
        "perecivel": True,
        "unidade_medida_id": test_database["unidade_id"],
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
    }
    response = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    criado = response.json()
    assert criado["codigo"] == "P-PERECIVEL-SEM-LOTE"
    assert criado["perecivel"] is True
    assert criado["total_lotes"] == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_crud_e_filtros_produto(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa criação de produto com composição, busca com filtros e imutabilidade de validade."""
    validade = date.today() + timedelta(days=20)

    # 1. Criação de produto perecível válido
    payload = {
        "codigo": "P-QUEIJO-PRATO",
        "nome": "Queijo Prato Especial",
        "descricao": "Queijo maturado fatiado",
        "preco": 32.50,
        "perecivel": True,
        "unidade_medida_id": test_database["unidade_id"],
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
        "lote_inicial": {
            "numero_lote": "LOTE-QP-01",
            "data_producao": str(date.today()),
            "data_validade": str(validade),
        },
        "nutrientes": [{"nome": "Cálcio", "unidade": "mg", "valor": 700.0}],
        "ingredientes": [
            {"ingrediente_id": test_database["ingrediente_id"], "ordem": 1}
        ],
        "alergeno_ids": [test_database["alergeno_id"]],
    }
    response = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    produto = response.json()
    assert produto["codigo"] == "P-QUEIJO-PRATO"
    assert produto["preco"] == 32.50
    assert produto["status"] == "zerado"
    produto_id = produto["id"]

    # 2. Listagem com filtros (por nome, faixa de preço)
    response = await client.get(
        "/api/v1/produtos",
        params={"nome": "Queijo", "preco_min": 30.0, "preco_max": 35.0},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    resultado = response.json()
    assert resultado["total"] >= 1
    assert any(p["id"] == produto_id for p in resultado["items"])

    # 3. Integridade referencial: Não permitir alterar data de validade diretamente no produto
    response_update = await client.put(
        f"/api/v1/produtos/{produto_id}",
        json={"data_validade": str(validade + timedelta(days=5))},
        headers=auth_headers,
    )
    assert response_update.status_code == 422

    # 4. Atualização 
    response_update_ok = await client.put(
        f"/api/v1/produtos/{produto_id}",
        json={"nome": "Queijo Prato Premium", "preco": 34.00},
        headers=auth_headers,
    )
    assert response_update_ok.status_code == 200, response_update_ok.text
    assert response_update_ok.json()["nome"] == "Queijo Prato Premium"
    assert response_update_ok.json()["preco"] == 34.00

    # 5. Exclusão de produto zerado (sem saldo)
    response_delete = await client.delete(
        f"/api/v1/produtos/{produto_id}", headers=auth_headers
    )
    assert response_delete.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_erros_404_produto_inexistente(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa que operações em produto inexistente retornam 404."""
    id_inexistente = 999999
    # GET 404
    get_resp = await client.get(f"/api/v1/produtos/{id_inexistente}", headers=auth_headers)
    assert get_resp.status_code == 404

    # PUT 404
    put_resp = await client.put(
        f"/api/v1/produtos/{id_inexistente}",
        json={"nome": "Nome Produto Inexistente"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 404

    # DELETE 404
    del_resp = await client.delete(f"/api/v1/produtos/{id_inexistente}", headers=auth_headers)
    assert del_resp.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_produto_codigo_duplicado_retorna_409(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que cadastrar produto com código já existente retorna 409 Conflict."""
    payload = {
        "codigo": "P-CODIGO-DUP",
        "nome": "Produto Base Duplicado",
        "preco": 10.0,
        "perecivel": False,
        "unidade_medida_id": test_database["unidade_id"],
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
    }
    # Primeiro cadastro: 201
    resp1 = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert resp1.status_code == 201

    # Segundo cadastro com o mesmo código: 409
    resp2 = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert resp2.status_code == 409
    assert "já existe" in resp2.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_produto_referencia_invalida_retorna_400(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que FK inválida de categoria/unidade/localização retorna 400 Bad Request."""
    payload = {
        "codigo": "P-REF-INVALIDA",
        "nome": "Produto Referência Inexistente",
        "preco": 15.0,
        "perecivel": False,
        "unidade_medida_id": 999999,  # Unidade inexistente
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
    }
    response = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "não existe" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_produto_ingrediente_ou_alergeno_invalido_retorna_400(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que ingrediente ou alérgeno inexistente retorna 400 Bad Request."""
    payload = {
        "codigo": "P-ING-INVALIDO",
        "nome": "Produto Ingrediente Inexistente",
        "preco": 20.0,
        "perecivel": False,
        "unidade_medida_id": test_database["unidade_id"],
        "categoria_id": test_database["categoria_id"],
        "localizacao_id": test_database["localizacao_id"],
        "ingredientes": [{"ingrediente_id": 999999, "ordem": 1}],
    }
    response = await client.post("/api/v1/produtos", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "não existe" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_filtros_produtos_invalidos_retornam_422(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa validações de filtro de busca: preco_min > preco_max e status inválido."""
    # 1. preco_min > preco_max
    resp_preco = await client.get(
        "/api/v1/produtos",
        params={"preco_min": 50.0, "preco_max": 20.0},
        headers=auth_headers,
    )
    assert resp_preco.status_code == 422
    assert "Preço mínimo maior que o máximo" in resp_preco.json()["detail"]

    # 2. status inválido
    resp_status = await client.get(
        "/api/v1/produtos",
        params={"status": "status_inexistente"},
        headers=auth_headers,
    )
    assert resp_status.status_code == 422
    assert "Status de produto inválido" in resp_status.json()["detail"]

