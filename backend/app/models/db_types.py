"""Tipos PostgreSQL sem equivalente nativo direto no SQLAlchemy."""

from typing import Any, cast

from sqlalchemy.dialects.postgresql.base import ischema_names
from sqlalchemy.types import TypeEngine, UserDefinedType


class PostgreSQLPoint(UserDefinedType[object]):
    """Tipo geométrico POINT usado pelo dump de cidades do IBGE."""

    cache_ok = True

    def get_col_spec(self, **kw: object) -> str:
        return "POINT"


cast(dict[str, type[TypeEngine[Any]]], ischema_names).setdefault(
    "point", PostgreSQLPoint
)
PG_POINT = PostgreSQLPoint()
