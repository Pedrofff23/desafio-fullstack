"""Rotas de CRUD de produtos e lotes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import CATALOGS_TAG, LOTS_TAG, PRODUCTS_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.produto import (
    ListaCatalogo,
    LoteCreate,
    LoteOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
)
from app.services.produto_service import ProdutoService

router = APIRouter(prefix="/produtos")


@router.get(
    "/catalogo",
    status_code=status.HTTP_200_OK,
    tags=[CATALOGS_TAG],
    summary="Listar dados auxiliares de produtos",
)
async def catalogo(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> ListaCatalogo:
    return await ProdutoService(db).catalogo()


@router.get(
    "",
    response_model=PaginatedResponse[ProdutoOut],
    status_code=status.HTTP_200_OK,
    tags=[PRODUCTS_TAG],
    summary="Listar produtos",
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Parâmetros de filtro inválidos"
        },
    },
)
async def listar(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    nome: str | None = None,
    status: str | None = None,
    preco_min: float | None = Query(None, ge=0),
    preco_max: float | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> PaginatedResponse[ProdutoOut]:
    return await ProdutoService(db).listar(
        page=page,
        size=size,
        nome=nome,
        status=status,
        preco_min=preco_min,
        preco_max=preco_max,
    )


@router.post(
    "",
    response_model=ProdutoOut,
    status_code=status.HTTP_201_CREATED,
    tags=[PRODUCTS_TAG],
    summary="Cadastrar produto",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Referências inválidas"},
        status.HTTP_409_CONFLICT: {"description": "Código de produto já existe"},
    },
)
async def criar(
    payload: ProdutoCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ProdutoOut:
    # O funcionário responsável é derivado do usuário autenticado.
    return await ProdutoService(db).criar(
        payload, funcionario_id=current.funcionario_id
    )


@router.get(
    "/{produto_id}",
    response_model=ProdutoOut,
    status_code=status.HTTP_200_OK,
    tags=[PRODUCTS_TAG],
    summary="Obter produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
    },
)
async def obter(
    produto_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> ProdutoOut:
    return await ProdutoService(db).obter(produto_id)


@router.put(
    "/{produto_id}",
    response_model=ProdutoOut,
    status_code=status.HTTP_200_OK,
    tags=[PRODUCTS_TAG],
    summary="Atualizar produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
        status.HTTP_409_CONFLICT: {"description": "Código já em uso por outro produto"},
    },
)
async def atualizar(
    produto_id: int,
    payload: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> ProdutoOut:
    return await ProdutoService(db).atualizar(produto_id, payload)


@router.delete(
    "/{produto_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=[PRODUCTS_TAG],
    summary="Excluir produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
    },
)
async def excluir(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MessageResponse:
    await ProdutoService(db).excluir(produto_id, excluido_por=current.id)
    return MessageResponse(message="Produto excluído com sucesso.")


# ---------------------------------------------------------------------------
# Lotes
# ---------------------------------------------------------------------------


@router.get(
    "/{produto_id}/lotes",
    response_model=list[LoteOut],
    status_code=status.HTTP_200_OK,
    tags=[LOTS_TAG],
    summary="Listar lotes de um produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
    },
)
async def listar_lotes(
    produto_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[LoteOut]:
    return await ProdutoService(db).listar_lotes(produto_id)


@router.post(
    "/{produto_id}/lotes",
    response_model=LoteOut,
    status_code=status.HTTP_201_CREATED,
    tags=[LOTS_TAG],
    summary="Cadastrar lote de um produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
        status.HTTP_409_CONFLICT: {"description": "Lote já cadastrado"},
    },
)
async def criar_lote(
    produto_id: int,
    payload: LoteCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> LoteOut:
    return await ProdutoService(db).criar_lote(produto_id, payload)
