"""Ponto de entrada da aplicação FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logger = logging.getLogger("estoque.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import db_manager

    db_manager.init()

    if settings.AUTO_MIGRATE:
        def _run_migrations() -> None:
            from alembic import command
            from alembic.config import Config

            cfg = Config("alembic.ini")
            command.upgrade(cfg, "head")

        import asyncio

        try:
            # Rodar alembic em thread separada (usa seu próprio event loop/engine)
            await asyncio.to_thread(_run_migrations)
            logger.info("Migrações Alembic aplicadas automaticamente")
        except Exception as e:  # noqa: BLE001
            logger.warning("Falha ao aplicar migrações automaticamente: %s", e)

    yield
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Sistema"])
async def health_check():
    from sqlalchemy import text

    from app.core.database import db_manager

    db_status = "ok"
    try:
        async with db_manager.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "error"
    return {"status": "ok", "version": settings.APP_VERSION, "database": db_status}