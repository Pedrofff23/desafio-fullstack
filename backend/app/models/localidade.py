"""Models de localidades: Pais, Estado, Cidade, Endereco, Contato.

Estas tabelas vêm dos dumps IBGE (pais.sql, estado.sql, cidade.sql) e são a
base para o endereço dos usuários/funcionários.
"""

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Pais(Base):
    __tablename__ = "paises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(60))
    nome_pt: Mapped[str | None] = mapped_column(String(60))
    sigla: Mapped[str | None] = mapped_column(String(2))
    bacen: Mapped[int | None] = mapped_column(Integer)
    ddi: Mapped[int | None] = mapped_column(Integer)

    estados: Mapped[list["Estado"]] = relationship(back_populates="pais_rel")


class Estado(Base):
    __tablename__ = "estados"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(60))
    uf: Mapped[str | None] = mapped_column(String(2))
    ibge: Mapped[int | None] = mapped_column(Integer)
    pais: Mapped[int | None] = mapped_column(ForeignKey("paises.id"))
    ddd: Mapped[list | None] = mapped_column(JSON)

    pais_rel: Mapped["Pais | None"] = relationship(back_populates="estados")
    cidades: Mapped[list["Cidade"]] = relationship(back_populates="estado")


class Cidade(Base):
    __tablename__ = "cidades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[int | None] = mapped_column(ForeignKey("estados.id"))
    ibge: Mapped[int | None] = mapped_column(Integer)
    lat_lon: Mapped[str | None] = mapped_column(Text)  # point
    cod_tom: Mapped[int | None] = mapped_column(Integer, default=0)

    estado: Mapped["Estado | None"] = relationship(back_populates="cidades")


class Endereco(Base):
    __tablename__ = "enderecos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    logradouro: Mapped[str] = mapped_column(String(150), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(100))
    cep: Mapped[str] = mapped_column(String(8), nullable=False)
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade_id: Mapped[int] = mapped_column(
        ForeignKey("cidades.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "logradouro", "numero", "complemento", "cep", "bairro", "cidade_id"
        ),
    )

    cidade: Mapped["Cidade"] = relationship()


class Contato(Base):
    __tablename__ = "contatos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo_pais: Mapped[str] = mapped_column(String(4), default="+55", nullable=False)
    ddd: Mapped[str] = mapped_column(String(2), nullable=False)
    numero: Mapped[str] = mapped_column(String(15), nullable=False)

    __table_args__ = (
        UniqueConstraint("codigo_pais", "ddd", "numero"),
    )