import asyncio
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.exc import DBAPIError

from app.core.database import db_manager
from app.models.transacao import RegistroEntrada


@pytest.mark.asyncio(loop_scope="session")
async def test_fornecedor_cadastro_e_validacao(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa cadastro de fornecedor com endereço e contato válidos."""
    payload = {
        "nome_empresa": "Distribuidora de Alimentos LTDA",
        "ativo": True,
        "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "977776666"},
        "endereco": {
            "logradouro": "Avenida dos Fornecedores",
            "numero": "500",
            "complemento": "Galpão 2",
            "cep": "03003000",
            "bairro": "Mooca",
            "estado_id": test_database["estado_id"],
            "cidade_id": test_database["cidade_id"],
        },
    }
    response = await client.post(
        "/api/v1/transacoes/fornecedores", json=payload, headers=auth_headers
    )
    assert response.status_code == 201, response.text
    fornecedor = response.json()
    assert fornecedor["nome_empresa"] == "Distribuidora de Alimentos LTDA"
    assert fornecedor["contato"]["numero"] == "977776666"


@pytest.mark.asyncio(loop_scope="session")
async def test_ciclo_estoque_entrada_saida_e_concorrencia(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa entrada, saída, concorrência, consulta de estoque e regras de auditoria."""
    # 1. Cria fornecedor
    fornecedor_resp = await client.post(
        "/api/v1/transacoes/fornecedores",
        headers=auth_headers,
        json={
            "nome_empresa": "Fornecedor Estoque Teste",
            "contato": {"codigo_pais": "+55", "ddd": "11", "numero": "933332222"},
            "endereco": {
                "logradouro": "Rua Fornecedor",
                "numero": "12",
                "cep": "01001000",
                "bairro": "Centro",
                "estado_id": test_database["estado_id"],
                "cidade_id": test_database["cidade_id"],
            },
        },
    )
    assert fornecedor_resp.status_code == 201
    fornecedor_id = fornecedor_resp.json()["id"]

    # 2. Cria produto para o teste
    validade = date.today() + timedelta(days=15)
    prod_resp = await client.post(
        "/api/v1/produtos",
        headers=auth_headers,
        json={
            "codigo": "P-ESTOQUE-TESTE",
            "nome": "Produto Movimento Estoque",
            "preco": 25.0,
            "perecivel": True,
            "unidade_medida_id": test_database["unidade_id"],
            "categoria_id": test_database["categoria_id"],
            "localizacao_id": test_database["localizacao_id"],
            "lote_inicial": {
                "numero_lote": "LOTE-EST-01",
                "data_producao": str(date.today()),
                "data_validade": str(validade),
            },
        },
    )
    assert prod_resp.status_code == 201
    produto_id = prod_resp.json()["id"]

    # Busca o lote gerado
    lotes_resp = await client.get(
        f"/api/v1/produtos/{produto_id}/lotes", headers=auth_headers
    )
    lote_id = lotes_resp.json()[0]["id"]

    # 3. Entrada de Estoque (10 unidades)
    entrada_resp = await client.post(
        "/api/v1/transacoes/entrada",
        headers=auth_headers,
        json={
            "lote_id": lote_id,
            "fornecedor_id": fornecedor_id,
            "quantidade": 10.0,
            "tipo_entrada": "compra",
            "observacao": "Entrada teste de estoque",
            "preco_custo": 15.0,
        },
    )
    assert entrada_resp.status_code == 201, entrada_resp.text
    entrada_id = entrada_resp.json()["id"]

    # 4. Verifica entradas disponíveis
    disp_resp = await client.get(
        "/api/v1/transacoes/entradas-disponiveis",
        params={"produto_id": produto_id},
        headers=auth_headers,
    )
    assert disp_resp.status_code == 200
    assert any(e["entrada_id"] == entrada_id and e["quantidade"] == 10.0 for e in disp_resp.json())

    # 5. Concorrência: duas saídas simultâneas de 7 unidades quando só existem 10
    # Uma deve ser aprovada (201) e a outra deve ser rejeitada (400) por saldo insuficiente
    async def realizar_saida():
        return await client.post(
            "/api/v1/transacoes/saida",
            headers=auth_headers,
            json={
                "entrada_id": entrada_id,
                "quantidade": 7.0,
                "tipo_saida": "venda",
                "preco_venda": 25.0,
            },
        )

    respostas = await asyncio.gather(realizar_saida(), realizar_saida())
    status_codes = sorted([r.status_code for r in respostas])
    assert status_codes == [201, 400]

    # 6. Verifica saldo restante (deve ser exatamente 3 unidades)
    saldo_resp = await client.get("/api/v1/transacoes/estoque", headers=auth_headers)
    assert saldo_resp.status_code == 200
    linha_estoque = next(
        item for item in saldo_resp.json()["items"] if item["produto_id"] == produto_id
    )
    assert linha_estoque["quantidade"] == 3.0

    # 7. Regra de integridade: Não permitir exclusão de produto com saldo em estoque
    delete_bloqueado = await client.delete(
        f"/api/v1/produtos/{produto_id}", headers=auth_headers
    )
    assert delete_bloqueado.status_code == 409

    # 8. Saída dos 3 restantes para zerar o saldo
    saida_zerar = await client.post(
        "/api/v1/transacoes/saida",
        headers=auth_headers,
        json={
            "entrada_id": entrada_id,
            "quantidade": 3.0,
            "tipo_saida": "venda",
            "preco_venda": 25.0,
        },
    )
    assert saida_zerar.status_code == 201

    # 9. Agora que o saldo está zerado, exclusão deve ser permitida
    delete_ok = await client.delete(
        f"/api/v1/produtos/{produto_id}", headers=auth_headers
    )
    assert delete_ok.status_code == 200

    # 10. Auditoria e transparência: Histórico de movimentações é preservado
    hist_resp = await client.get(
        "/api/v1/transacoes/historico",
        params={"produto_id": produto_id},
        headers=auth_headers,
    )
    assert hist_resp.status_code == 200
    historico = hist_resp.json()
    assert historico["total"] >= 2  # Entrada + saídas registradas

    # 11. Auditoria e transparência: Transações não podem ser deletadas do banco (trigger/restrição)
    async with db_manager.sessionmaker() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                delete(RegistroEntrada).where(RegistroEntrada.id == entrada_id)
            )
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio(loop_scope="session")
async def test_erros_e_validacoes_de_transacoes(
    client: AsyncClient, auth_headers: dict[str, str], test_database: dict
):
    """Testa erros 404 e 422 em entradas e saídas de estoque."""
    # 1. Entrada com lote inexistente -> 404
    entrada_sem_lote = await client.post(
        "/api/v1/transacoes/entrada",
        headers=auth_headers,
        json={
            "lote_id": 999999,
            "fornecedor_id": 1,
            "quantidade": 10.0,
            "tipo_entrada": "compra",
            "preco_custo": 10.0,
        },
    )
    assert entrada_sem_lote.status_code == 404

    # 2. Saída com entrada inexistente -> 404
    saida_sem_entrada = await client.post(
        "/api/v1/transacoes/saida",
        headers=auth_headers,
        json={
            "entrada_id": 999999,
            "quantidade": 1.0,
            "tipo_saida": "venda",
            "preco_venda": 10.0,
        },
    )
    assert saida_sem_entrada.status_code == 404

    # 3. Saída com quantidade inválida (<= 0) -> 422
    saida_qtd_zero = await client.post(
        "/api/v1/transacoes/saida",
        headers=auth_headers,
        json={
            "entrada_id": 1,
            "quantidade": 0.0,
            "tipo_saida": "venda",
            "preco_venda": 10.0,
        },
    )
    assert saida_qtd_zero.status_code == 422

    # 4. Histórico com filtros por tipo
    hist_resp = await client.get(
        "/api/v1/transacoes/historico",
        params={"tipo": "entrada"},
        headers=auth_headers,
    )
    assert hist_resp.status_code == 200
    for mov in hist_resp.json()["items"]:
        assert mov["tipo"] == "entrada"

