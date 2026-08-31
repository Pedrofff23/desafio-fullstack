"""Models de catálogo e estoque físico: UnidadeMedida, Categoria, Alergeno,
Ingrediente, Corredor, Seccao, Prateleira, LocalizacaoEstoque, Produto, Lote."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UnidadeMedida(Base):
    __tablename__ = "unidades_medida"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    sigla: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200))


class Alergeno(Base):
    __tablename__ = "alergenos"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200))


class Ingrediente(Base):
    __tablename__ = "ingredientes"

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200))


class Corredor(Base):
    __tablename__ = "corredores"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(100))


class Seccao(Base):
    __tablename__ = "seccoes"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    corredor_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("corredores.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (UniqueConstraint("corredor_id", "nome"),)


class Prateleira(Base):
    __tablename__ = "prateleiras"

    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    seccao_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("seccoes.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    nivel: Mapped[int | None] = mapped_column(SmallInteger)
    descricao: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (UniqueConstraint("seccao_id", "nome"),)


class LocalizacaoEstoque(Base):
    __tablename__ = "localizacoes_estoque"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    prateleira_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("prateleiras.id"), unique=True, nullable=False
    )


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    preco: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    perecivel: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    unidade_medida_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("unidades_medida.id"), nullable=False
    )
    categoria_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("categorias.id"), nullable=False
    )
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey("localizacoes_estoque.id"), nullable=False
    )
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, server_default=true(), nullable=False
    )
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    unidade_medida: Mapped["UnidadeMedida"] = relationship()
    categoria: Mapped["Categoria"] = relationship()
    localizacao: Mapped["LocalizacaoEstoque"] = relationship()
    lotes: Mapped[list["Lote"]] = relationship(back_populates="produto")

    __table_args__ = (Index("idx_produto_categoria", "categoria_id"),)


class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    numero_lote: Mapped[str] = mapped_column(String(50), nullable=False)
    data_producao: Mapped[date] = mapped_column(Date, nullable=False)
    data_validade: Mapped[date | None] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(
        Boolean, server_default=true(), nullable=False
    )
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    __table_args__ = (
        UniqueConstraint("produto_id", "numero_lote"),
        Index("idx_lote_validade", "data_validade"),
    )

    produto: Mapped["Produto"] = relationship(back_populates="lotes")


class Nutriente(Base):
    __tablename__ = "nutrientes"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)

    __table_args__ = (UniqueConstraint("produto_id", "nome"),)


class ProdutoIngrediente(Base):
    __tablename__ = "produtos_ingredientes"

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"), primary_key=True
    )
    ingrediente_id: Mapped[int] = mapped_column(
        ForeignKey("ingredientes.id"), primary_key=True
    )
    ordem: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    __table_args__ = (UniqueConstraint("produto_id", "ordem"),)


class ProdutoAlergeno(Base):
    __tablename__ = "produtos_alergenos"

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"), primary_key=True
    )
    alergeno_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("alergenos.id"), primary_key=True
    )
