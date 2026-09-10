import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_crud_completo_fornecedor(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa criação, listagem, busca por ID, atualização e exclusão de fornecedor."""
    # 1. Criação
    payload = {
        "nome_empresa": "Fornecedor Alpha Alimentos",
        "ativo": True,
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "987654321"},
        "endereco": {
            "logradouro": "Rua das Indústrias",
            "numero": "123",
            "complemento": "Galpão A",
            "cep": "01001000",
            "bairro": "Distrito Industrial",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    response = await client.post(
        "/api/v1/transacoes/fornecedores", json=payload, headers=auth_headers
    )
    assert response.status_code == 201, response.text
    fornecedor = response.json()
    assert fornecedor["nome_empresa"] == "Fornecedor Alpha Alimentos"
    assert fornecedor["contato"]["numero"] == "987654321"
    fornecedor_id = fornecedor["id"]

    # 2. Listagem
    list_resp = await client.get(
        "/api/v1/transacoes/fornecedores", headers=auth_headers
    )
    assert list_resp.status_code == 200, list_resp.text
    fornecedores = list_resp.json()
    assert any(f["id"] == fornecedor_id for f in fornecedores)

    # 3. Busca por ID
    get_resp = await client.get(
        f"/api/v1/transacoes/fornecedores/{fornecedor_id}", headers=auth_headers
    )
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["nome_empresa"] == "Fornecedor Alpha Alimentos"

    # 4. Atualização
    update_payload = {"nome_empresa": "Fornecedor Alpha Alimentos Renomeado"}
    put_resp = await client.put(
        f"/api/v1/transacoes/fornecedores/{fornecedor_id}",
        json=update_payload,
        headers=auth_headers,
    )
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["nome_empresa"] == "Fornecedor Alpha Alimentos Renomeado"

    # 5. Exclusão (Soft delete)
    del_resp = await client.delete(
        f"/api/v1/transacoes/fornecedores/{fornecedor_id}", headers=auth_headers
    )
    assert del_resp.status_code == 200, del_resp.text

    # 6. Verificação pós-exclusão
    get_apos_del = await client.get(
        f"/api/v1/transacoes/fornecedores/{fornecedor_id}", headers=auth_headers
    )
    assert get_apos_del.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_cadastrar_fornecedor_com_endereco_ibge_invalido_retorna_400(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Garante que endereço de fornecedor com cidade e estado incompatíveis retorne 400."""
    payload = {
        "nome_empresa": "Fornecedor Inválido",
        "ativo": True,
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988887777"},
        "endereco": {
            "logradouro": "Rua Errada",
            "numero": "456",
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["outro_estado_id"],  # RJ
            "cidade_id": test_database["cidade_id"],        # SP
        },
    }
    response = await client.post(
        "/api/v1/transacoes/fornecedores", json=payload, headers=auth_headers
    )
    assert response.status_code == 400
    assert "não pertence ao estado" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_erros_404_fornecedor_inexistente(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa que operações de busca, atualização e exclusão em ID inexistente retornam 404."""
    id_inexistente = 999999
    # GET 404
    get_resp = await client.get(
        f"/api/v1/transacoes/fornecedores/{id_inexistente}", headers=auth_headers
    )
    assert get_resp.status_code == 404

    # PUT 404
    put_resp = await client.put(
        f"/api/v1/transacoes/fornecedores/{id_inexistente}",
        json={"nome_empresa": "Qualquer Nome"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 404

    # DELETE 404
    del_resp = await client.delete(
        f"/api/v1/transacoes/fornecedores/{id_inexistente}", headers=auth_headers
    )
    assert del_resp.status_code == 404

