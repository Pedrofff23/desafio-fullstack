from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação lidas a partir de variáveis de ambiente /.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco de dados
    DATABASE_URL: str = (
        "postgresql+asyncpg://estoque:estoque123@db:5432/gerenciamento_estoque"
    )

    # Segurança / JWT
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Migrations
    AUTO_MIGRATE: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:5173"]

    # Aplicação
    APP_NAME: str = "Gerenciamento de Estoque API"
    APP_VERSION: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
