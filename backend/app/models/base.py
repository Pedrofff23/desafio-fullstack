from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    """Base declarativa para todos os models com convenção de nomenclatura padronizada."""

    metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)


class TimestampMixin:
    """Adiciona colunas de auditoria de criação."""

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
