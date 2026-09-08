"""Model de lote de produto."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.produto import Produto

class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    numero_lote: Mapped[str] = mapped_column(String(50), nullable=False)
    data_producao: Mapped[date] = mapped_column(Date, nullable=False)
    data_validade: Mapped[date | None] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    __table_args__ = (
        UniqueConstraint(
            "produto_id", "numero_lote", name="lotes_produto_id_numero_lote_key"
        ),
        Index("idx_lote_validade", "data_validade"),
    )

    produto: Mapped["Produto"] = relationship(back_populates="lotes")  # noqa: F821
