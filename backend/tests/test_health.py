import pytest
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_health_check_endpoint(client: AsyncClient):
    """Testa a saúde da aplicação conforme o endpoint /health.

    Este é o teste mais fundamental da API (equivalente ao test_read_main da documentação do FastAPI).
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert "version" in data
