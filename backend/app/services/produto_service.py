"""Service de produtos e catálogos auxiliares.

Responsável pelo CRUD, pela composição alimentícia e pelo saldo dos produtos.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote import Lote
from app.models.produto import (
    Nutriente,
    Produto,
    ProdutoAlergeno,
    ProdutoIngrediente,
)
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.produto import (
    AlergenoOut,
    CategoriaOut,
    IngredienteOut,
    ListaCatalogo,
    LocalizacaoOut,
    NutrienteInput,
    NutrienteOut,
    ProdutoCreate,
    ProdutoIngredienteInput,
    ProdutoIngredienteOut,
    ProdutoOut,
    ProdutoUpdate,
    UnidadeMedidaOut,
)

LIMIAR_ESTOQUE_BAIXO = 5
STATUS_VALIDOS = {"ok", "estoque_baixo", "zerado"}


class ProdutoService:
    """Regras de negócio do módulo de produtos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProdutoRepository(session)

    # ------------------------------------------------------------------
    # Montagem dos DTOs
    # ------------------------------------------------------------------
    def _enrich(
        self,
        produto: Produto,
        quantidade: float = 0,
        total_lotes: int = 0,
    ) -> ProdutoOut:
        status = "ok"
        if quantidade <= 0:
            status = "zerado"
        elif quantidade < LIMIAR_ESTOQUE_BAIXO:
            status = "estoque_baixo"

        return ProdutoOut(
            id=produto.id,
            codigo=produto.codigo,
            nome=produto.nome,
            descricao=produto.descricao,
            preco=float(produto.preco),
            perecivel=produto.perecivel,
            unidade_medida_id=produto.unidade_medida_id,
            categoria_id=produto.categoria_id,
            localizacao_id=produto.localizacao_id,
            ativo=produto.ativo,
            unidade_medida=(
                UnidadeMedidaOut.model_validate(
                    produto.unidade_medida, from_attributes=True
                )
                if produto.unidade_medida
                else None
            ),
            categoria=(
                CategoriaOut.model_validate(produto.categoria, from_attributes=True)
                if produto.categoria
                else None
            ),
            quantidade_estoque=quantidade,
            status=status,
            total_lotes=total_lotes,
            nutrientes=[
                NutrienteOut(
                    id=nutriente.id,
                    nome=nutriente.nome,
                    unidade=nutriente.unidade,
                    valor=float(nutriente.valor),
                )
                for nutriente in produto.nutrientes
            ],
            ingredientes=[
                ProdutoIngredienteOut(
                    ingrediente_id=associacao.ingrediente_id,
                    ordem=associacao.ordem,
                    nome=associacao.ingrediente.nome,
                    descricao=associacao.ingrediente.descricao,
                )
                for associacao in produto.ingredientes_associacoes
            ],
            alergenos=[
                AlergenoOut.model_validate(associacao.alergeno, from_attributes=True)
                for associacao in produto.alergenos_associacoes
            ],
        )

    @staticmethod
    def _localizacao_out(localizacao) -> LocalizacaoOut:
        prateleira = localizacao.prateleira
        seccao = prateleira.seccao
        return LocalizacaoOut(
            id=localizacao.id,
            prateleira_id=localizacao.prateleira_id,
            corredor=seccao.corredor.nome,
            seccao=seccao.nome,
            prateleira=prateleira.nome,
            nivel=prateleira.nivel,
            descricao=prateleira.descricao,
        )

    async def _validate_food_references(
        self,
        ingredientes: list[ProdutoIngredienteInput],
        alergeno_ids: list[int],
    ) -> None:
        validas = await self.repo.validate_food_references(
            {item.ingrediente_id for item in ingredientes}, set(alergeno_ids)
        )
        if not validas:
            raise HTTPException(
                status_code=400,
                detail="Ingrediente ou alérgeno informado não existe",
            )

    @staticmethod
    def _apply_composition(
        produto: Produto,
        *,
        nutrientes: list[NutrienteInput] | None = None,
        ingredientes: list[ProdutoIngredienteInput] | None = None,
        alergeno_ids: list[int] | None = None,
    ) -> None:
        if nutrientes is not None:
            produto.nutrientes = [Nutriente(**item.model_dump()) for item in nutrientes]
        if ingredientes is not None:
            produto.ingredientes_associacoes = [
                ProdutoIngrediente(**item.model_dump()) for item in ingredientes
            ]
        if alergeno_ids is not None:
            produto.alergenos_associacoes = [
                ProdutoAlergeno(alergeno_id=alergeno_id) for alergeno_id in alergeno_ids
            ]

    async def _replace_composition(
        self,
        produto: Produto,
        *,
        nutrientes: list[NutrienteInput] | None,
        ingredientes: list[ProdutoIngredienteInput] | None,
        alergeno_ids: list[int] | None,
    ) -> None:
        if nutrientes is not None:
            produto.nutrientes.clear()
        if ingredientes is not None:
            produto.ingredientes_associacoes.clear()
        if alergeno_ids is not None:
            produto.alergenos_associacoes.clear()
        if any(item is not None for item in (nutrientes, ingredientes, alergeno_ids)):
            await self.session.flush()
        if nutrientes is not None:
            produto.nutrientes.extend(
                Nutriente(**item.model_dump()) for item in nutrientes
            )
        if ingredientes is not None:
            produto.ingredientes_associacoes.extend(
                ProdutoIngrediente(**item.model_dump()) for item in ingredientes
            )
        if alergeno_ids is not None:
            produto.alergenos_associacoes.extend(
                ProdutoAlergeno(alergeno_id=alergeno_id) for alergeno_id in alergeno_ids
            )

    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    async def get_catalog(self) -> ListaCatalogo:
        unidades = await self.repo.list_unidades()
        categorias = await self.repo.list_categorias()
        localizacoes = await self.repo.list_localizacoes()
        ingredientes = await self.repo.list_ingredientes()
        alergenos = await self.repo.list_alergenos()
        return ListaCatalogo.model_validate(
            {
                "unidades_medida": unidades,
                "categorias": categorias,
                "localizacoes": [self._localizacao_out(item) for item in localizacoes],
                "ingredientes": [
                    IngredienteOut.model_validate(item, from_attributes=True)
                    for item in ingredientes
                ],
                "alergenos": [
                    AlergenoOut.model_validate(item, from_attributes=True)
                    for item in alergenos
                ],
            }
        )

    # ------------------------------------------------------------------
    # Listagem com filtros
    # ------------------------------------------------------------------
    async def list(
        self,
        page: int = 1,
        size: int = 20,
        nome: str | None = None,
        status: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> PaginatedResponse[ProdutoOut]:
        if preco_min is not None and preco_max is not None and preco_min > preco_max:
            raise HTTPException(
                status_code=422, detail="Preço mínimo maior que o máximo"
            )
        if status is not None and status not in STATUS_VALIDOS:
            raise HTTPException(status_code=422, detail="Status de produto inválido")

        itens, total, saldos, lotes_counts = await self.repo.list_paginated(
            page=page,
            size=size,
            nome=nome,
            status=status,
            preco_min=preco_min,
            preco_max=preco_max,
        )
        out = [
            self._enrich(
                p,
                saldos.get(p.id, 0.0),
                lotes_counts.get(p.id, 0),
            )
            for p in itens
        ]
        return PaginatedResponse.build(out, total, page, size)

    async def get(self, produto_id: int) -> ProdutoOut:
        produto = await self.repo.get_com_relacionamentos(produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        saldos = await self.repo.get_product_balances([produto.id])
        lotes_counts = await self.repo.count_product_lots([produto.id])
        return self._enrich(
            produto,
            saldos.get(produto.id, 0.0),
            lotes_counts.get(produto.id, 0),
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create(self, data: ProdutoCreate, funcionario_id: int) -> ProdutoOut:
        if await self.repo.get_by_codigo(data.codigo):
            raise HTTPException(status_code=409, detail="Código de produto já existe")
        if not await self.repo.validate_references(
            data.unidade_medida_id, data.categoria_id, data.localizacao_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Unidade, categoria ou localização informada não existe",
            )
        await self._validate_food_references(
            data.ingredientes, data.alergeno_ids
        )
        lote_inicial = data.lote_inicial
        produto = Produto(
            **data.model_dump(
                exclude={
                    "lote_inicial",
                    "nutrientes",
                    "ingredientes",
                    "alergeno_ids",
                }
            ),
            funcionario_id=funcionario_id,
        )
        self._apply_composition(
            produto,
            nutrientes=data.nutrientes,
            ingredientes=data.ingredientes,
            alergeno_ids=data.alergeno_ids,
        )
        try:
            await self.repo.add(produto)
            if lote_inicial is not None:
                await self.repo.add_lote(
                    Lote(produto_id=produto.id, **lote_inicial.model_dump())
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Produto ou lote já cadastrado"
            ) from exc
        return await self.get(produto.id)

    async def update(self, produto_id: int, data: ProdutoUpdate) -> ProdutoOut:
        produto = await self.repo.get_com_relacionamentos(produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        valores = data.model_dump(
            exclude_unset=True,
            exclude={"nutrientes", "ingredientes", "alergeno_ids"},
        )
        codigo = valores.get("codigo")
        if codigo is not None and codigo != produto.codigo:
            existente = await self.repo.get_by_codigo(codigo)
            if existente is not None:
                raise HTTPException(
                    status_code=409, detail="Código de produto já existe"
                )
        if not await self.repo.validate_references(
            valores.get("unidade_medida_id", produto.unidade_medida_id),
            valores.get("categoria_id", produto.categoria_id),
            valores.get("localizacao_id", produto.localizacao_id),
        ):
            raise HTTPException(
                status_code=400,
                detail="Unidade, categoria ou localização informada não existe",
            )
        ingredientes = (
            data.ingredientes if "ingredientes" in data.model_fields_set else None
        )
        alergeno_ids = (
            data.alergeno_ids if "alergeno_ids" in data.model_fields_set else None
        )
        await self._validate_food_references(
            ingredientes or [], alergeno_ids or []
        )
        try:
            for k, v in valores.items():
                setattr(produto, k, v)
            await self._replace_composition(
                produto,
                nutrientes=(
                    data.nutrientes if "nutrientes" in data.model_fields_set else None
                ),
                ingredientes=ingredientes,
                alergeno_ids=alergeno_ids,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail="Não foi possível atualizar o produto"
            ) from exc
        return await self.get(produto_id)

    async def delete(self, produto_id: int, deleted_by: int | None = None) -> None:
        produto = await self.repo.get_for_update(produto_id)
        if produto is None or produto.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        saldos = await self.repo.get_product_balances([produto_id])
        if saldos.get(produto_id, 0) > 0:
            raise HTTPException(
                status_code=409,
                detail="Não é possível excluir produto com saldo em estoque",
            )
        produto.ativo = False
        await self.repo.soft_delete(produto_id, deleted_by)
        await self.session.commit()
