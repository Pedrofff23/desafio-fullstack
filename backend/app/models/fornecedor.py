"""Model de fornecedor."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.localidade import Contato, Endereco


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    nome_empresa: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    contato_id: Mapped[int] = mapped_column(ForeignKey("contatos.id"), nullable=False)
    endereco_id: Mapped[int] = mapped_column(ForeignKey("enderecos.id"), nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    contato: Mapped["Contato"] = relationship()
    endereco: Mapped["Endereco"] = relationship()
