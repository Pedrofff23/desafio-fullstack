"""Ponto de entrada da aplicação FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.openapi import API_DESCRIPTION, OPENAPI_TAGS, SYSTEM_TAG
from app.api.v1 import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import db_manager

    db_manager.init()

    if settings.AUTO_MIGRATE:

        def _run_migrations() -> None:
            from alembic.config import Config

            from alembic import command

            cfg = Config("alembic.ini")
            command.upgrade(cfg, "head")

        import asyncio

        # Falha de migration impede a API de iniciar sobre um schema incompleto.
        await asyncio.to_thread(_run_migrations)

    yield
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    description=API_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=[SYSTEM_TAG], summary="Verificar a saúde da aplicação")
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
