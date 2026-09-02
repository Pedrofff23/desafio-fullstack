"""Rotas de CRUD de produtos e lotes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.produto import (
    LoteCreate,
    LoteOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
)
from app.services.produto_service import ProdutoService

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("/catalogo")
async def catalogo(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ProdutoService(db).catalogo()


@router.get("", response_model=PaginatedResponse[ProdutoOut])
async def listar(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    nome: str | None = None,
    status: str | None = None,
    preco_min: float | None = Query(None, ge=0),
    preco_max: float | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ProdutoService(db).listar(
        page=page,
        size=size,
        nome=nome,
        status=status,
        preco_min=preco_min,
        preco_max=preco_max,
    )


@router.post("", response_model=ProdutoOut, status_code=201)
async def criar(
    payload: ProdutoCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    # O funcionário responsável é derivado do usuário autenticado.
    return await ProdutoService(db).criar(
        payload, funcionario_id=current.funcionario_id
    )


@router.get("/{produto_id}", response_model=ProdutoOut)
async def obter(
    produto_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await ProdutoService(db).obter(produto_id)


@router.put("/{produto_id}", response_model=ProdutoOut)
async def atualizar(
    produto_id: int,
    payload: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ProdutoService(db).atualizar(produto_id, payload)


@router.delete("/{produto_id}", response_model=MessageResponse)
async def excluir(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    await ProdutoService(db).excluir(produto_id, excluido_por=current.id)
    return MessageResponse(message="Produto excluído com sucesso.")


# ---------------------------------------------------------------------------
# Lotes
# ---------------------------------------------------------------------------


@router.get("/{produto_id}/lotes", response_model=list[LoteOut])
async def listar_lotes(
    produto_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await ProdutoService(db).listar_lotes(produto_id)


@router.post("/{produto_id}/lotes", response_model=LoteOut, status_code=201)
async def criar_lote(
    produto_id: int,
    payload: LoteCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ProdutoService(db).criar_lote(produto_id, payload)
