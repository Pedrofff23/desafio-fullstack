"""Tipos PostgreSQL sem equivalente nativo direto no SQLAlchemy."""

from sqlalchemy.dialects.postgresql.base import ischema_names
from sqlalchemy.types import UserDefinedType


class PostgreSQLPoint(UserDefinedType):
    """Tipo geométrico POINT usado pelo dump de cidades do IBGE."""

    cache_ok = True

    def get_col_spec(self, **kw: object) -> str:
        return "POINT"


ischema_names.setdefault("point", PostgreSQLPoint)
PG_POINT = PostgreSQLPoint()
