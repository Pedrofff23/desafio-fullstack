"""Repositório de movimentações e consultas de estoque."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, literal, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote import Lote
from app.models.produto import Produto
from app.models.transacao import RegistroEntrada, RegistroSaida
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository

# Alias para legibilidade das queries de histórico
Entrada = RegistroEntrada


class TransacaoRepository(BaseRepository[RegistroEntrada]):
    """Acesso a dados de movimentações de estoque."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RegistroEntrada, session)

    # ------------------------------------------------------------------
    # Entradas
    # ------------------------------------------------------------------
    async def get_entrada(self, entrada_id: int) -> RegistroEntrada | None:
        return await self.get(entrada_id)

    async def add_entrada(self, entrada: RegistroEntrada) -> RegistroEntrada:
        return await self.add(entrada)

    # ------------------------------------------------------------------
    # Saídas
    # ------------------------------------------------------------------
    async def add_saida(self, saida: RegistroSaida) -> RegistroSaida:
        self.session.add(saida)
        await self.session.flush()
        return saida

    # ------------------------------------------------------------------
    # Saldos (views criadas na migration)
    # ------------------------------------------------------------------
    async def get_saldo_entrada(self, entrada_id: int) -> float:
        row = await self.session.execute(
            text("""
                SELECT COALESCE(quantidade, 0)
                FROM estoque_entrada
                WHERE entrada_id = :eid
                """),
            {"eid": entrada_id},
        )
        return float(row.scalar() or 0)

    async def list_entradas_disponiveis(
        self, produto_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Lista entradas que ainda possuem saldo para uma futura saída."""

        filtro_produto = (
            " AND ee.produto_id = :produto_id" if produto_id is not None else ""
        )
        query = text(f"""
            SELECT
                ee.entrada_id,
                ee.lote_id,
                ee.produto_id,
                ee.fornecedor_id,
                ee.localizacao_id,
                ee.quantidade
            FROM estoque_entrada ee
            JOIN lotes l ON l.id = ee.lote_id
            JOIN produtos p ON p.id = ee.produto_id
            WHERE ee.quantidade > 0 AND p.ativo AND l.ativo
              AND p.excluido_em IS NULL AND l.excluido_em IS NULL{filtro_produto}
            ORDER BY ee.produto_id, ee.lote_id, ee.entrada_id
            """)
        params = {"produto_id": produto_id} if produto_id is not None else {}
        rows = await self.session.execute(query, params)
        return [
            {
                "entrada_id": int(row[0]),
                "lote_id": int(row[1]),
                "produto_id": int(row[2]),
                "fornecedor_id": int(row[3]),
                "localizacao_id": int(row[4]),
                "quantidade": float(row[5]),
            }
            for row in rows.fetchall()
        ]

    async def get_estoque_atual_by_produto(
        self, *, page: int = 1, size: int = 20, nome: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        """Retorna o estoque agregado com paginação executada no PostgreSQL."""

        where_clause = "WHERE p.excluido_em IS NULL"
        params: dict[str, Any] = {"size": size, "offset": (page - 1) * size}
        if nome:
            where_clause += " AND p.nome ILIKE :nome"
            params["nome"] = f"%{nome}%"

        total = int(
            await self.session.scalar(
                text(f"SELECT COUNT(*) FROM produtos p {where_clause}"),
                params,
            )
            or 0
        )
        rows = await self.session.execute(
            text(f"""
                WITH pagina_produtos AS (
                    SELECT p.id, p.nome
                    FROM produtos p
                    {where_clause}
                    ORDER BY p.nome, p.id
                    LIMIT :size OFFSET :offset
                )
                SELECT
                    pp.id,
                    pp.nome,
                    COALESCE(e.qtd, 0) AS qtd,
                    COALESCE(l.total_lotes, 0) AS total_lotes,
                    COALESCE(lv.lotes_vencendo, 0) AS lotes_vencendo,
                    COALESCE(lv.lotes_vencidos, 0) AS lotes_vencidos
                FROM pagina_produtos pp
                LEFT JOIN (
                    SELECT ep.produto_id, SUM(ep.quantidade) AS qtd
                    FROM estoque_produto ep
                    WHERE ep.produto_id IN (SELECT id FROM pagina_produtos)
                    GROUP BY ep.produto_id
                ) e ON e.produto_id = pp.id
                LEFT JOIN (
                    SELECT lote.produto_id, COUNT(lote.id) AS total_lotes
                    FROM lotes lote
                    WHERE lote.excluido_em IS NULL
                      AND lote.produto_id IN (SELECT id FROM pagina_produtos)
                    GROUP BY lote.produto_id
                ) l ON l.produto_id = pp.id
                LEFT JOIN (
                    SELECT
                        lote.produto_id,
                        COUNT(CASE WHEN lote.data_validade IS NOT NULL AND lote.data_validade >= CURRENT_DATE AND lote.data_validade < (CURRENT_DATE + 30) THEN 1 END) AS lotes_vencendo,
                        COUNT(CASE WHEN lote.data_validade IS NOT NULL AND lote.data_validade < CURRENT_DATE THEN 1 END) AS lotes_vencidos
                    FROM lotes lote
                    JOIN estoque_produto ep
                      ON ep.lote_id = lote.id
                     AND ep.produto_id = lote.produto_id
                     AND ep.quantidade > 0
                    WHERE lote.excluido_em IS NULL
                      AND lote.produto_id IN (SELECT id FROM pagina_produtos)
                    GROUP BY lote.produto_id
                ) lv ON lv.produto_id = pp.id
                ORDER BY pp.nome, pp.id
                """),
            params,
        )
        itens = [
            {
                "produto_id": r[0],
                "produto_nome": r[1],
                "quantidade": float(r[2]),
                "total_lotes": int(r[3]),
                "lotes_vencendo": int(r[4]),
                "lotes_vencidos": int(r[5]),
            }
            for r in rows.fetchall()
        ]
        return itens, total

    # ------------------------------------------------------------------
    # Histórico — unifica entradas e saídas em uma lista
    # ------------------------------------------------------------------
    async def get_historico(
        self,
        *,
        page: int = 1,
        size: int = 20,
        produto_id: int | None = None,
        tipo: str | None = None,
        funcionario_id: int | None = None,
        quantidade: float | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        entradas = select(
            RegistroEntrada.id.label("id"),
            literal("entrada").label("tipo"),
            RegistroEntrada.tipo_entrada.label("tipo_movimento"),
            Lote.produto_id.label("produto_id"),
            RegistroEntrada.lote_id.label("lote_id"),
            RegistroEntrada.quantidade.label("quantidade"),
            RegistroEntrada.data_entrada.label("data_movimento"),
            RegistroEntrada.preco_custo.label("preco"),
            RegistroEntrada.observacao.label("observacao"),
            RegistroEntrada.funcionario_id.label("funcionario_id"),
        ).join(Lote, Lote.id == RegistroEntrada.lote_id)

        saidas = (
            select(
                RegistroSaida.id.label("id"),
                literal("saida").label("tipo"),
                RegistroSaida.tipo_saida.label("tipo_movimento"),
                Lote.produto_id.label("produto_id"),
                Entrada.lote_id.label("lote_id"),
                RegistroSaida.quantidade.label("quantidade"),
                RegistroSaida.data_saida.label("data_movimento"),
                RegistroSaida.preco_venda.label("preco"),
                literal(None).label("observacao"),
                RegistroSaida.funcionario_id.label("funcionario_id"),
            )
            .join(
                Entrada,
                Entrada.id == RegistroSaida.entrada_id,
            )
            .join(
                Lote,
                Lote.id == Entrada.lote_id,
            )
        )

        unidos = union_all(entradas, saidas).subquery()

        base = (
            select(
                unidos,
                Produto.nome.label("produto_nome"),
                Usuario.email.label("responsavel_email"),
            )
            .outerjoin(Produto, Produto.id == unidos.c.produto_id)
            .outerjoin(Usuario, Usuario.funcionario_id == unidos.c.funcionario_id)
        )
        count = select(func.count()).select_from(unidos)

        if produto_id is not None:
            base = base.where(unidos.c.produto_id == produto_id)
            count = count.where(unidos.c.produto_id == produto_id)
        if tipo is not None:
            base = base.where(unidos.c.tipo == tipo)
            count = count.where(unidos.c.tipo == tipo)
        if funcionario_id is not None:
            base = base.where(unidos.c.funcionario_id == funcionario_id)
            count = count.where(unidos.c.funcionario_id == funcionario_id)
        if quantidade is not None:
            base = base.where(unidos.c.quantidade == quantidade)
            count = count.where(unidos.c.quantidade == quantidade)
        if data_inicio is not None:
            base = base.where(unidos.c.data_movimento >= data_inicio)
            count = count.where(unidos.c.data_movimento >= data_inicio)
        if data_fim is not None:
            base = base.where(unidos.c.data_movimento <= data_fim)
            count = count.where(unidos.c.data_movimento <= data_fim)

        base = base.order_by(unidos.c.data_movimento.desc())
        base = base.offset((page - 1) * size).limit(size)

        rows = (await self.session.execute(base)).mappings().all()
        total = int((await self.session.execute(count)).scalar() or 0)
        return [dict(r) for r in rows], total
