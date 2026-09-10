import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.fixture
async def produto_base(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
) -> int:
    """Fixture auxiliar para criar um produto base com validade de teste."""
    validade = date.today() + timedelta(days=45)
    codigo = f"P-LOTE-{uuid.uuid4().hex[:6].upper()}"
    resp = await client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "codigo": codigo,
            "nome": "Produto Teste Lotes",
            "preco": 10.0,
            "perecivel": True,
            "unidade_medida_id": test_database["unidade_id"],
            "categoria_id": test_database["categoria_id"],
            "localizacao_id": test_database["localizacao_id"],
            "lote_inicial": {
                "numero_lote": f"LOTE-INI-{uuid.uuid4().hex[:4].upper()}",
                "data_producao": str(date.today()),
                "data_validade": str(validade),
            },
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_criar_e_listar_lotes_de_produto(
    client: AsyncClient, auth_headers: dict[str, str], produto_base: int
):
    """Testa criação de um novo lote avulso para produto existente e listagem dos lotes."""
    validade = date.today() + timedelta(days=20)
    payload = {
        "numero_lote": "LOTE-EXTRA-02",
        "data_producao": str(date.today()),
        "data_validade": str(validade),
        "ativo": True,
    }
    response = await client.post(
        f"/api/v1/produtos/{produto_base}/lotes",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    lote = response.json()
    assert lote["numero_lote"] == "LOTE-EXTRA-02"
    assert lote["status_validade"] == "validade_proxima"  # < 30 dias

    # Listar lotes do produto
    lista_resp = await client.get(
        f"/api/v1/produtos/{produto_base}/lotes", headers=auth_headers
    )
    assert lista_resp.status_code == 200
    lotes = lista_resp.json()
    assert len(lotes) >= 2


@pytest.mark.asyncio(loop_scope="session")
async def test_obter_e_atualizar_lote(
    client: AsyncClient, auth_headers: dict[str, str], produto_base: int
):
    """Testa busca detalhada e atualização de lote."""
    validade = date.today() + timedelta(days=60)
    criado = await client.post(
        f"/api/v1/produtos/{produto_base}/lotes",
        json={
            "numero_lote": "LOTE-UPDATE-03",
            "data_producao": str(date.today()),
            "data_validade": str(validade),
        },
        headers=auth_headers,
    )
    assert criado.status_code == 201
    lote_id = criado.json()["id"]

    # Obter lote
    get_resp = await client.get(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}", headers=auth_headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["numero_lote"] == "LOTE-UPDATE-03"

    # Atualizar lote
    put_resp = await client.put(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}",
        json={"numero_lote": "LOTE-UPDATE-03-MODIFICADO"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["numero_lote"] == "LOTE-UPDATE-03-MODIFICADO"


@pytest.mark.asyncio(loop_scope="session")
async def test_excluir_lote_sem_estoque_sucesso(
    client: AsyncClient, auth_headers: dict[str, str], produto_base: int
):
    """Testa exclusão de lote que não possui saldo em estoque."""
    validade = date.today() + timedelta(days=30)
    criado = await client.post(
        f"/api/v1/produtos/{produto_base}/lotes",
        json={
            "numero_lote": "LOTE-PARA-DELETAR",
            "data_producao": str(date.today()),
            "data_validade": str(validade),
        },
        headers=auth_headers,
    )
    assert criado.status_code == 201
    lote_id = criado.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}", headers=auth_headers
    )
    assert del_resp.status_code == 200

    # Busca subsequente deve dar 404
    get_resp = await client.get(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}", headers=auth_headers
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_erros_e_validacoes_de_lote(
    client: AsyncClient, auth_headers: dict[str, str], produto_base: int
):
    """Testa regras de negócio: produto 404, duplicidade 409, perecível sem data 422."""
    validade = date.today() + timedelta(days=10)

    # 1. Produto inexistente -> 404
    p_404 = await client.post(
        "/api/v1/produtos/999999/lotes",
        json={
            "numero_lote": "LOTE-X",
            "data_producao": str(date.today()),
            "data_validade": str(validade),
        },
        headers=auth_headers,
    )
    assert p_404.status_code == 404

    # 2. Perecível sem data de validade -> 422
    p_sem_val = await client.post(
        f"/api/v1/produtos/{produto_base}/lotes",
        json={"numero_lote": "LOTE-SEM-VALIDADE", "data_producao": str(date.today())},
        headers=auth_headers,
    )
    assert p_sem_val.status_code == 422

    # 3. Lote com número duplicado para o mesmo produto -> 409
    lotes_resp = await client.get(
        f"/api/v1/produtos/{produto_base}/lotes", headers=auth_headers
    )
    lote_existente = lotes_resp.json()[0]
    p_dup = await client.post(
        f"/api/v1/produtos/{produto_base}/lotes",
        json={
            "numero_lote": lote_existente["numero_lote"],
            "data_producao": str(date.today()),
            "data_validade": str(validade),
        },
        headers=auth_headers,
    )
    assert p_dup.status_code == 409

    # 4. Data de validade anterior à produção no update -> 422
    lote_id = lote_existente["id"]
    update_invalido = await client.put(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}",
        json={
            "data_producao": str(date.today()),
            "data_validade": str(date.today() - timedelta(days=1)),
        },
        headers=auth_headers,
    )
    assert update_invalido.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_excluir_lote_com_estoque_retorna_409(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict, produto_base: int
):
    """Regra de integridade: Não é permitido excluir lote que possua saldo em estoque."""
    # 1. Cria fornecedor
    forn_resp = await client.post(
        "/api/v1/transacoes/fornecedores",
        headers=auth_headers,
        json={
            "nome_empresa": f"Fornecedor Lote Teste {uuid.uuid4().hex[:4]}",
            "ativo": True,
            "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988880000"},
            "endereco": {
                "logradouro": "Rua Lote",
                "numero": "10",
                "cep": "01001000",
                "bairro": "Centro",
                "estado_id": test_database["estado_id"],
                "cidade_id": test_database["cidade_id"],
            },
        },
    )
    assert forn_resp.status_code == 201
    fornecedor_id = forn_resp.json()["id"]

    # 2. Pega o lote do produto
    lotes_resp = await client.get(
        f"/api/v1/produtos/{produto_base}/lotes", headers=auth_headers
    )
    lote_id = lotes_resp.json()[0]["id"]

    # 3. Registra entrada de estoque
    entrada_resp = await client.post(
        "/api/v1/transacoes/entrada",
        headers=auth_headers,
        json={
            "lote_id": lote_id,
            "fornecedor_id": fornecedor_id,
            "quantidade": 5.0,
            "tipo_entrada": "compra",
            "observacao": "Teste exclusao lote com saldo",
            "preco_custo": 10.0,
        },
    )
    assert entrada_resp.status_code == 201

    # 4. Tenta excluir o lote com saldo -> deve retornar 409
    del_resp = await client.delete(
        f"/api/v1/produtos/{produto_base}/lotes/{lote_id}", headers=auth_headers
    )
    assert del_resp.status_code == 409
    assert "Não é possível excluir lote com saldo em estoque" in del_resp.json()["detail"]
