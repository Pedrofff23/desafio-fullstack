import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_cidades_por_estado_ibge(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa integração com as tabelas de IBGE (listar cidades por estado)."""
    estado_id = test_database["estado_id"]
    response = await client.get(
        f"/api/v1/geo/estados/{estado_id}/cidades",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    cidades = response.json()
    assert len(cidades) > 0
    assert cidades[0]["estado_id"] == estado_id


@pytest.mark.asyncio(loop_scope="session")
async def test_validacao_endereco_ibge_invalido_retorna_400(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa cadastrar usuário com uma cidade que não pertence ao estado retorna 400."""
    payload = {
        "nome": "Usuário Endereço Inválido",
        "email": "invalido@teste.com",
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "911111111"},
        "endereco": {
            "logradouro": "Rua Errada",
            "numero": "100",
            "complemento": None,
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["outro_estado_id"],  # RJ
            "cidade_id": test_database["cidade_id"],        # São Paulo (não pertence ao RJ)
        },
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "não pertence ao estado" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_crud_completo_usuario(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa fluxo completo de CRUD do usuário: criação, busca, atualização e remoção."""
    # 1. Criação
    payload = {
        "nome": "Carlos Silva",
        "email": "CARLOS@TESTE.COM",  # Teste de normalização para minúsculo
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988776655"},
        "endereco": {
            "logradouro": "Avenida Paulista",
            "numero": "1000",
            "complemento": "Apto 101",
            "cep": "01310100",
            "bairro": "Bela Vista",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    criado = response.json()
    assert criado["email"] == "carlos@teste.com"
    assert criado["funcionario"]["nome_completo"] == "Carlos Silva"
    usuario_id = criado["id"]

    # 2. Listagem com filtro
    response = await client.get(
        "/api/v1/usuarios", params={"nome": "Carlos"}, headers=auth_headers
    )
    assert response.status_code == 200
    lista = response.json()
    assert lista["total"] >= 1
    assert any(u["id"] == usuario_id for u in lista["items"])

    # 3. Atualização
    update_payload = {"nome": "Carlos Silva Atualizado"}
    response = await client.put(
        f"/api/v1/usuarios/{usuario_id}", json=update_payload, headers=auth_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["funcionario"]["nome_completo"] == "Carlos Silva Atualizado"

    # 4. Detalhe
    response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["funcionario"]["nome_completo"] == "Carlos Silva Atualizado"

    # 5. Exclusão (Soft Delete)
    response = await client.delete(f"/api/v1/usuarios/{usuario_id}", headers=auth_headers)
    assert response.status_code == 200

    # 6. Verificação de exclusão (404)
    response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_cadastro_email_duplicado_retorna_409(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que cadastrar usuário com email já existente retorna 409 Conflict."""
    payload = {
        "nome": "Usuário Duplicado",
        "email": "operador@teste.com",  # email já existe no seed
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "912345678"},
        "endereco": {
            "logradouro": "Rua Exemplo",
            "numero": "10",
            "complemento": None,
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert response.status_code == 409
    assert "já cadastrado" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_erros_404_usuario_inexistente(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa que operações em usuário inexistente retornam 404."""
    id_inexistente = 999999
    # GET 404
    get_resp = await client.get(f"/api/v1/usuarios/{id_inexistente}", headers=auth_headers)
    assert get_resp.status_code == 404

    # PUT 404
    put_resp = await client.put(
        f"/api/v1/usuarios/{id_inexistente}",
        json={"nome": "Nome Novo"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 404

    # DELETE 404
    del_resp = await client.delete(f"/api/v1/usuarios/{id_inexistente}", headers=auth_headers)
    assert del_resp.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_atualizar_usuario_email_duplicado_retorna_409(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que atualizar o e-mail de um usuário para um e-mail já existente retorna 409."""
    # Cria usuário secundário
    payload = {
        "nome": "Usuário Para Atualizar",
        "email": "secundario_update@teste.com",
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988771122"},
        "endereco": {
            "logradouro": "Rua Exemplo",
            "numero": "100",
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    criado = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert criado.status_code == 201
    user_id = criado.json()["id"]

    # Tenta atualizar o e-mail para o e-mail do operador@teste.com
    put_resp = await client.put(
        f"/api/v1/usuarios/{user_id}",
        json={"email": "operador@teste.com"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 409
    assert "já cadastrado" in put_resp.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_atualizar_usuario_endereco_invalido_retorna_400(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que atualizar endereço com combinação inválida de cidade e estado retorna 400."""
    payload = {
        "nome": "Usuário Endereço Teste",
        "email": "endereco_update@teste.com",
        "senha": "Senha123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "988773344"},
        "endereco": {
            "logradouro": "Rua Valida",
            "numero": "20",
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    criado = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert criado.status_code == 201
    user_id = criado.json()["id"]

    # Atualiza endereço para cidade e estado incompatíveis
    put_resp = await client.put(
        f"/api/v1/usuarios/{user_id}",
        json={
            "endereco": {
                "logradouro": "Rua Modificada",
                "numero": "30",
                "cep": "01001000",
                "bairro": "Centro",
                "estado_id": test_database["outro_estado_id"],
                "cidade_id": test_database["cidade_id"],
            }
        },
        headers=auth_headers,
    )
    assert put_resp.status_code == 400
    assert "não pertence ao estado" in put_resp.json()["detail"]

