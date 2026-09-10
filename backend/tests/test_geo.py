import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_estados(client: AsyncClient, auth_headers: dict[str, str]):
    """Testa endpoint GET /api/v1/geo/estados."""
    response = await client.get("/api/v1/geo/estados", headers=auth_headers)
    assert response.status_code == 200, response.text
    estados = response.json()
    assert isinstance(estados, list)
    assert len(estados) > 0
    primeiro = estados[0]
    assert "id" in primeiro
    assert "nome" in primeiro
    assert "uf" in primeiro
    assert "ibge" in primeiro


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_cidades_por_estado_valido(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa endpoint GET /api/v1/geo/estados/{estado_id}/cidades com estado válido."""
    estado_id = test_database["estado_id"]
    response = await client.get(
        f"/api/v1/geo/estados/{estado_id}/cidades",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    cidades = response.json()
    assert isinstance(cidades, list)
    assert len(cidades) > 0
    assert all(c["estado_id"] == estado_id for c in cidades)


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_cidades_estado_inexistente_retorna_404(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Testa endpoint GET /api/v1/geo/estados/{estado_id}/cidades com ID inexistente."""
    response = await client.get(
        "/api/v1/geo/estados/999999/cidades",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "Estado não encontrado" in response.json()["detail"]

