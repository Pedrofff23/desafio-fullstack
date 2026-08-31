"""Models de movimentações e fornecedores: Fornecedor, RegistroEntrada,
RegistroSaida."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.localidade import Contato, Endereco
from app.models.produto import Lote, LocalizacaoEstoque


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    nome_empresa: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    contato_id: Mapped[int] = mapped_column(ForeignKey("contatos.id"), nullable=False)
    endereco_id: Mapped[int] = mapped_column(ForeignKey("enderecos.id"), nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, server_default=true(), nullable=False
    )
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    contato: Mapped["Contato"] = relationship()
    endereco: Mapped["Endereco"] = relationship()


class RegistroEntrada(Base):
    __tablename__ = "registros_entrada"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False
    )
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey("localizacoes_estoque.id"), nullable=False
    )
    quantidade: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    data_entrada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    tipo_entrada: Mapped[str] = mapped_column(
        String(50), server_default="compra", nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(Text)
    preco_custo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    preco_sugerido: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=False
    )

    lote: Mapped["Lote"] = relationship()
    fornecedor: Mapped["Fornecedor"] = relationship()
    localizacao: Mapped["LocalizacaoEstoque"] = relationship()
    saidas: Mapped[list["RegistroSaida"]] = relationship(back_populates="entrada")

    __table_args__ = (
        Index("idx_entrada_data", "data_entrada"),
        Index("idx_entrada_fornecedor", "fornecedor_id"),
        Index("idx_entrada_lote", "lote_id"),
        Index("idx_entrada_localizacao", "localizacao_id"),
    )


class RegistroSaida(Base):
    __tablename__ = "registros_saida"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    entrada_id: Mapped[int] = mapped_column(
        ForeignKey("registros_entrada.id"), nullable=False
    )
    quantidade: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    data_saida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    tipo_saida: Mapped[str] = mapped_column(
        String(50), server_default="venda", nullable=False
    )
    preco_venda: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=False
    )

    entrada: Mapped["RegistroEntrada"] = relationship(back_populates="saidas")

    __table_args__ = (
        Index("idx_saida_data", "data_saida"),
        Index("idx_saida_entrada", "entrada_id"),
    )
