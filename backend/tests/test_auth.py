import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_login_sucesso_retorna_token(client: AsyncClient):
    """Testa o endpoint de login com credenciais válidas."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "operador@teste.com", "senha": "Senha123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_invalido_retorna_401(client: AsyncClient):
    """Testa o endpoint de login com senha incorreta."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "operador@teste.com", "senha": "SenhaErrada"},
    )
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_obter_usuario_logado_sem_token_retorna_401(client: AsyncClient):
    """Testa endpoint protegido sem cabeçalho Authorization."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_obter_usuario_logado_com_token_retorna_perfil(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa endpoint protegido com token JWT válido."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "operador@teste.com"
    assert data["funcionario"]["nome_completo"] == "Usuário Operador"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_usuario_inativo_retorna_401(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa que usuário desativado ou excluído não consegue se autenticar."""
    # 1. Cria usuário
    email = "inativo_auth@teste.com"
    payload = {
        "nome": "Usuário Para Inativar",
        "email": email,
        "senha": "SenhaValida123",
        "perfil": "funcionario",
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "999881122"},
        "endereco": {
            "logradouro": "Rua Inativo",
            "numero": "1",
            "cep": "01001000",
            "bairro": "Centro",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    create_resp = await client.post("/api/v1/usuarios", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # 2. Exclui/Inativa o usuário
    del_resp = await client.delete(f"/api/v1/usuarios/{user_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # 3. Tenta login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "senha": "SenhaValida123"},
    )
    assert login_resp.status_code == 401
    assert "inativo ou excluído" in login_resp.json()["detail"]

