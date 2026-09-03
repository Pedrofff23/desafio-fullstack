"""Repositório de usuários e funcionários."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.localidade import Cidade, Contato, Endereco
from app.models.usuario import Funcionario, Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    """Acesso a dados de usuários (e entidades vinculadas)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Usuario, session)

    async def get_by_email(self, email: str) -> Usuario | None:
        stmt = select(Usuario).where(
            Usuario.email == email, Usuario.excluido_em.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_including_inactive(self, email: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_funcionario(self, funcionario_id: int) -> Funcionario | None:
        return await self.session.get(Funcionario, funcionario_id)

    async def get_endereco(self, endereco_id: int) -> Endereco | None:
        return await self.session.get(Endereco, endereco_id)

    async def get_contato(self, contato_id: int) -> Contato | None:
        return await self.session.get(Contato, contato_id)

    async def get_cidade(self, cidade_id: int) -> Cidade | None:
        return await self.session.get(Cidade, cidade_id)

    async def cidade_pertence_ao_estado(self, cidade_id: int, estado_id: int) -> bool:
        result = await self.session.execute(
            select(Cidade.id).where(Cidade.id == cidade_id, Cidade.uf == estado_id)
        )
        return result.scalar_one_or_none() is not None

    async def listar_paginado(
        self, *, page: int = 1, size: int = 20, nome: str | None = None
    ) -> tuple[list[Usuario], int]:
        """Busca paginada de usuários com filtros no banco."""
        stmt = (
            select(Usuario)
            .where(Usuario.excluido_em.is_(None))
            .options(
                selectinload(Usuario.funcionario)
                .selectinload(Funcionario.endereco)
                .selectinload(Endereco.cidade),
                selectinload(Usuario.funcionario).selectinload(Funcionario.contato),
            )
        )
        total_stmt = select(func.count(Usuario.id)).where(Usuario.excluido_em.is_(None))
        if nome:
            termo = f"%{nome.strip()}%"
            stmt = stmt.join(Usuario.funcionario).where(
                Funcionario.nome_completo.ilike(termo)
            )
            total_stmt = total_stmt.join(Usuario.funcionario).where(
                Funcionario.nome_completo.ilike(termo)
            )
        stmt = stmt.order_by(Usuario.id).offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        itens = list(result.scalars().unique().all())

        total = await self.session.execute(total_stmt)
        total_count = int(total.scalar() or 0)
        return itens, total_count
