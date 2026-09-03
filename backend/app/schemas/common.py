"""Schemas genéricos reutilizáveis: paginação e respostas de mensagem."""

from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    """Resposta paginada genérica."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(
        cls, items: list[T], total: int, page: int, size: int
    ) -> "PaginatedResponse[T]":
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class MessageResponse(BaseModel):
    """Resposta simples com mensagem."""

    message: str = Field(examples=["Operação realizada com sucesso."])
