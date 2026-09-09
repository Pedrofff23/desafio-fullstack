"""Rotas do CRUD de produtos e dos catálogos auxiliares."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import CATALOGS_TAG, PRODUCTS_TAG
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.produto import ListaCatalogo, ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services.produto_service import ProdutoService

router = APIRouter(prefix="/produtos")


@router.get(
    "/catalogo",
    status_code=status.HTTP_200_OK,
    tags=[CATALOGS_TAG],
    summary="Listar dados auxiliares de produtos",
)
async def get_catalog(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> ListaCatalogo:
    return await ProdutoService(db).get_catalog()


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
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    nome: str | None = None,
    status: str | None = None,
    preco_min: float | None = Query(None, ge=0),
    preco_max: float | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> PaginatedResponse[ProdutoOut]:
    return await ProdutoService(db).list(
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
async def create_product(
    payload: ProdutoCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ProdutoOut:
    # O funcionário responsável é derivado do usuário autenticado.
    return await ProdutoService(db).create(
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
async def get_product(
    produto_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> ProdutoOut:
    return await ProdutoService(db).get(produto_id)


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
async def update_product(
    produto_id: int,
    payload: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> ProdutoOut:
    return await ProdutoService(db).update(produto_id, payload)


@router.delete(
    "/{produto_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=[PRODUCTS_TAG],
    summary="Excluir produto",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Produto não encontrado"},
        status.HTTP_409_CONFLICT: {
            "description": "Produto ainda possui saldo em estoque"
        },
    },
)
async def delete_product(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MessageResponse:
    await ProdutoService(db).delete(produto_id, deleted_by=current.id)
    return MessageResponse(message="Produto excluído com sucesso.")
