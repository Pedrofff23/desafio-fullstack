"""Service transacional do CRUD de lotes."""

from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote import Lote
from app.repositories.lote_repository import LoteRepository
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.lote import LoteCreate, LoteLocalizacaoOut, LoteOut, LoteUpdate


class LoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LoteRepository(session)
        self.produto_repo = ProdutoRepository(session)

    @staticmethod
    def _to_out(lote: Lote, localizacoes: list[dict[str, Any]]) -> LoteOut:
        saldo = sum(float(item["quantidade"]) for item in localizacoes)
        dias = (lote.data_validade - date.today()).days if lote.data_validade else None
        if dias is None:
            status_validade = "sem_validade"
        elif dias < 0:
            status_validade = "vencido"
        elif dias < 30:
            status_validade = "validade_proxima"
        else:
            status_validade = "normal"
        return LoteOut(
            id=lote.id,
            produto_id=lote.produto_id,
            numero_lote=lote.numero_lote,
            data_producao=lote.data_producao,
            data_validade=lote.data_validade,
            ativo=lote.ativo,
            quantidade_estoque=saldo,
            status_estoque="com_estoque" if saldo > 0 else "sem_estoque",
            dias_para_vencer=dias,
            status_validade=status_validade,
            localizacoes=[LoteLocalizacaoOut.model_validate(x) for x in localizacoes],
        )

    async def _get_product(self, produto_id: int):
        produto = await self.produto_repo.get(produto_id)
        if produto is None or produto.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return produto

    async def list(self, produto_id: int) -> list[LoteOut]:
        await self._get_product(produto_id)
        lotes = await self.repo.list_by_product(produto_id)
        locais = await self.repo.localizacoes(produto_id)
        return [self._to_out(lote, locais.get(lote.id, [])) for lote in lotes]

    async def get(self, produto_id: int, lote_id: int) -> LoteOut:
        await self._get_product(produto_id)
        lote = await self.repo.get(produto_id, lote_id)
        if lote is None:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        locais = await self.repo.localizacoes(produto_id)
        return self._to_out(lote, locais.get(lote.id, []))

    async def create(self, produto_id: int, data: LoteCreate) -> LoteOut:
        produto = await self._get_product(produto_id)
        if produto.perecivel and data.data_validade is None:
            raise HTTPException(
                status_code=422,
                detail="Produto perecível exige data de validade no lote",
            )
        lote = Lote(produto_id=produto_id, **data.model_dump())
        try:
            await self.repo.add(lote)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Número de lote já cadastrado"
            ) from exc
        return await self.get(produto_id, lote.id)

    async def update(
        self, produto_id: int, lote_id: int, data: LoteUpdate
    ) -> LoteOut:
        produto = await self._get_product(produto_id)
        lote = await self.repo.get(produto_id, lote_id)
        if lote is None:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        valores = data.model_dump(exclude_unset=True)
        producao = valores.get("data_producao", lote.data_producao)
        validade = valores.get("data_validade", lote.data_validade)
        if validade is not None and validade < producao:
            raise HTTPException(
                status_code=422,
                detail="Data de validade não pode ser anterior à produção",
            )
        if produto.perecivel and validade is None:
            raise HTTPException(
                status_code=422,
                detail="Produto perecível exige data de validade no lote",
            )
        if valores.get("ativo") is False and await self.repo.saldo(lote_id) > 0:
            raise HTTPException(
                status_code=409,
                detail="Não é possível desativar lote com saldo em estoque",
            )
        for campo, valor in valores.items():
            setattr(lote, campo, valor)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Número de lote já cadastrado"
            ) from exc
        return await self.get(produto_id, lote_id)

    async def delete(
        self, produto_id: int, lote_id: int, excluido_por: int | None
    ) -> None:
        await self._get_product(produto_id)
        lote = await self.repo.get(produto_id, lote_id)
        if lote is None:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        if await self.repo.saldo(lote_id) > 0:
            raise HTTPException(
                status_code=409,
                detail="Não é possível excluir lote com saldo em estoque",
            )
        lote.ativo = False
        await self.repo.soft_delete(lote_id, excluido_por)
        await self.session.commit()
