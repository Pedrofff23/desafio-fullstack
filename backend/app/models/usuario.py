"""Models de usuários e autenticação: Funcionario, Usuario, Sessao."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.localidade import Contato, Endereco


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    endereco_id: Mapped[int] = mapped_column(
        ForeignKey("enderecos.id"), nullable=False
    )
    contato_id: Mapped[int] = mapped_column(ForeignKey("contatos.id"), nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    endereco: Mapped["Endereco"] = relationship()
    contato: Mapped["Contato"] = relationship()
    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="funcionario",
        foreign_keys="Usuario.funcionario_id"
    )


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default="funcionario")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    funcionario: Mapped["Funcionario"] = relationship(
        back_populates="usuario",
        foreign_keys="Usuario.funcionario_id"
    )
    sessoes: Mapped[list["Sessao"]] = relationship(back_populates="usuario")


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    data_expiracao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="sessoes")