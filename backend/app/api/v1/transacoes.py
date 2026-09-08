"""Rotas de movimentações de estoque, fornecedores e saldos."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.openapi import (
    INVENTORY_MOVEMENTS_TAG,
    INVENTORY_QUERIES_TAG,
    SUPPLIERS_TAG,
)
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.transacao import (
    EstoqueEntradaOut,
    EstoqueProdutoOut,
    FornecedorCreate,
    FornecedorOut,
    MovimentoOut,
    RegistroEntradaCreate,
    RegistroEntradaOut,
    RegistroSaidaCreate,
    RegistroSaidaOut,
)
from app.services.transacao_service import TransacaoService

router = APIRouter(prefix="/transacoes")


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------


@router.get(
    "/fornecedores",
    status_code=status.HTTP_200_OK,
    tags=[SUPPLIERS_TAG],
    summary="Listar fornecedores",
)
async def listar_fornecedores(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
) -> list[FornecedorOut]:
    return await TransacaoService(db).listar_fornecedores()


@router.post(
    "/fornecedores",
    response_model=FornecedorOut,
    status_code=status.HTTP_201_CREATED,
    tags=[SUPPLIERS_TAG],
    summary="Cadastrar fornecedor",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "A cidade informada não pertence ao estado selecionado"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Fornecedor, contato ou endereço já cadastrado"
        },
    },
)
async def criar_fornecedor(
    payload: FornecedorCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> FornecedorOut:
    return await TransacaoService(db).criar_fornecedor(payload)


# ---------------------------------------------------------------------------
# Entrada / Saída
# ---------------------------------------------------------------------------


@router.post(
    "/entrada",
    response_model=RegistroEntradaOut,
    status_code=status.HTTP_201_CREATED,
    tags=[INVENTORY_MOVEMENTS_TAG],
    summary="Registrar entrada de estoque",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Localização inválida ou não informada"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Lote, produto ou fornecedor não encontrado"
        },
    },
)
async def registrar_entrada(
    payload: RegistroEntradaCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> RegistroEntradaOut:
    return await TransacaoService(db).registrar_entrada(
        payload, funcionario_id=current.funcionario_id
    )


@router.post(
    "/saida",
    response_model=RegistroSaidaOut,
    status_code=status.HTTP_201_CREATED,
    tags=[INVENTORY_MOVEMENTS_TAG],
    summary="Registrar saída de estoque",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Saldo insuficiente para saída"},
        status.HTTP_404_NOT_FOUND: {"description": "Entrada de estoque não encontrada"},
    },
)
async def registrar_saida(
    payload: RegistroSaidaCreate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> RegistroSaidaOut:
    return await TransacaoService(db).registrar_saida(
        payload, funcionario_id=current.funcionario_id
    )


# ---------------------------------------------------------------------------
# Estoque atual e histórico
# ---------------------------------------------------------------------------


@router.get(
    "/entradas-disponiveis",
    response_model=list[EstoqueEntradaOut],
    status_code=status.HTTP_200_OK,
    tags=[INVENTORY_QUERIES_TAG],
    summary="Listar entradas com saldo disponível",
)
async def entradas_disponiveis(
    produto_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> list[EstoqueEntradaOut]:
    return await TransacaoService(db).entradas_disponiveis(produto_id=produto_id)


@router.get(
    "/estoque",
    response_model=PaginatedResponse[EstoqueProdutoOut],
    status_code=status.HTTP_200_OK,
    tags=[INVENTORY_QUERIES_TAG],
    summary="Consultar estoque atual por produto",
)
async def estoque_atual(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> PaginatedResponse[EstoqueProdutoOut]:
    return await TransacaoService(db).estoque_atual(page=page, size=size)


@router.get(
    "/historico",
    response_model=PaginatedResponse[MovimentoOut],
    status_code=status.HTTP_200_OK,
    tags=[INVENTORY_QUERIES_TAG],
    summary="Consultar histórico de movimentações",
)
async def historico(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    produto_id: int | None = None,
    tipo: str | None = None,
    funcionario_id: int | None = None,
    quantidade: float | None = Query(None, gt=0),
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> PaginatedResponse[MovimentoOut]:
    return await TransacaoService(db).historico(
        page=page,
        size=size,
        produto_id=produto_id,
        tipo=tipo,
        funcionario_id=funcionario_id,
        quantidade=quantidade,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
