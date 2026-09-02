"""Repositório de movimentações de estoque e fornecedores."""

from datetime import datetime

from sqlalchemy import func, literal, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.localidade import Endereco
from app.models.produto import Lote
from app.models.transacao import Fornecedor, RegistroEntrada, RegistroSaida
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
        return await self.session.get(RegistroEntrada, entrada_id)

    async def add_entrada(self, entrada: RegistroEntrada) -> RegistroEntrada:
        self.session.add(entrada)
        await self.session.flush()
        return entrada

    # ------------------------------------------------------------------
    # Saídas
    # ------------------------------------------------------------------
    async def add_saida(self, saida: RegistroSaida) -> RegistroSaida:
        self.session.add(saida)
        await self.session.flush()
        return saida

    # ------------------------------------------------------------------
    # Fornecedores
    # ------------------------------------------------------------------
    async def list_fornecedores(self) -> list[Fornecedor]:
        result = await self.session.execute(
            select(Fornecedor)
            .where(Fornecedor.excluido_em.is_(None))
            .options(
                selectinload(Fornecedor.contato),
                selectinload(Fornecedor.endereco).selectinload(Endereco.cidade),
            )
            .order_by(Fornecedor.nome_empresa)
        )
        return list(result.scalars().all())

    async def get_fornecedor(self, fornecedor_id: int) -> Fornecedor | None:
        result = await self.session.execute(
            select(Fornecedor)
            .where(
                Fornecedor.id == fornecedor_id,
                Fornecedor.excluido_em.is_(None),
            )
            .options(
                selectinload(Fornecedor.contato),
                selectinload(Fornecedor.endereco).selectinload(Endereco.cidade),
            )
        )
        return result.scalars().unique().one_or_none()

    async def add_fornecedor(self, fornecedor: Fornecedor) -> Fornecedor:
        self.session.add(fornecedor)
        await self.session.flush()
        return fornecedor

    # ------------------------------------------------------------------
    # Saldos (views criadas na migration)
    # ------------------------------------------------------------------
    async def saldo_entrada(self, entrada_id: int) -> float:
        row = await self.session.execute(
            text(
                """
                SELECT COALESCE(quantidade, 0)
                FROM estoque_entrada
                WHERE entrada_id = :eid
                """
            ),
            {"eid": entrada_id},
        )
        return float(row.scalar() or 0)

    async def saldo_produto(self, produto_id: int) -> float:
        row = await self.session.execute(
            text(
                """
                SELECT COALESCE(SUM(quantidade), 0)
                FROM estoque_produto
                WHERE produto_id = :pid
                """
            ),
            {"pid": produto_id},
        )
        return float(row.scalar() or 0)

    async def entradas_disponiveis(self, produto_id: int | None = None) -> list[dict]:
        """Lista entradas que ainda possuem saldo para uma futura saída."""

        filtro_produto = (
            " AND produto_id = :produto_id" if produto_id is not None else ""
        )
        query = text(
            f"""
            SELECT
                entrada_id,
                lote_id,
                produto_id,
                fornecedor_id,
                localizacao_id,
                quantidade
            FROM estoque_entrada
            WHERE quantidade > 0{filtro_produto}
            ORDER BY produto_id, lote_id, entrada_id
            """
        )
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

    async def estoque_atual_por_produto(self) -> list[dict]:
        """Linhas agregadas do estoque por produto (view estoque_produto)."""

        rows = await self.session.execute(
            text(
                """
                SELECT p.id, p.nome, COALESCE(e.qtd, 0) AS qtd
                FROM produtos p
                LEFT JOIN (
                    SELECT produto_id, SUM(quantidade) AS qtd
                    FROM estoque_produto
                    GROUP BY produto_id
                ) e ON e.produto_id = p.id
                WHERE p.excluido_em IS NULL
                ORDER BY p.nome, p.id
                """
            )
        )
        return [
            {"produto_id": r[0], "produto_nome": r[1], "quantidade": float(r[2])}
            for r in rows.fetchall()
        ]

    # ------------------------------------------------------------------
    # Histórico (auditoria) — unifica entradas e saídas em uma lista
    # ------------------------------------------------------------------
    async def historico(
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
    ) -> tuple[list[dict], int]:
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

        base = select(unidos)
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
