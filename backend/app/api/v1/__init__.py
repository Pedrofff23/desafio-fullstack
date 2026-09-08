"""Agrega todos os routers da API v1."""

from fastapi import APIRouter

from app.api.v1 import auth, fornecedores, geo, lotes, produtos, transacoes, usuarios

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(geo.router)
api_router.include_router(usuarios.router)
api_router.include_router(produtos.router)
api_router.include_router(lotes.router)
api_router.include_router(transacoes.router)
api_router.include_router(fornecedores.router)


__all__ = ["api_router"]
