"""Service de usuários: CRUD transacional com endereço, contato e funcionário.

Todo o cadastro/edição é feito dentro de UMA transação (commit único), garantindo
atomicidade entre as tabelas `enderecos`, `contatos`, `funcionarios` e `usuarios`.
"""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.usuario import Funcionario, Usuario
from app.repositories.localidade_repository import LocalidadeRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.common import PaginatedResponse
from app.schemas.usuario import (
    ContatoIn,
    EnderecoIn,
    UsuarioCreate,
    UsuarioOut,
    UsuarioUpdate,
)


def _contato_para_orm(data: ContatoIn) -> dict[str, str]:
    return {
        "codigo_pais": data.codigo_pais,
        "ddd": data.ddd,
        "numero": data.numero,
    }


def _endereco_para_orm(data: EnderecoIn) -> dict[str, str | int | None]:
    return {
        "logradouro": data.logradouro,
        "numero": data.numero,
        "complemento": data.complemento,
        "cep": data.cep,
        "bairro": data.bairro,
        "cidade_id": data.cidade_id,
    }


class UsuarioService:
    """Regras de negócio do módulo de usuários."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UsuarioRepository(session)
        self.localidade_repo = LocalidadeRepository(session)

    # ------------------------------------------------------------------
    # Helper de montagem do DTO
    # ------------------------------------------------------------------
    def _to_out(self, usuario: Usuario) -> UsuarioOut:
        # Relacionamentos já carregados via selectinload
        return UsuarioOut.model_validate(usuario, from_attributes=True)

    # ------------------------------------------------------------------
    # Validações de FK
    # ------------------------------------------------------------------
    async def _validar_endereco(self, endereco: EnderecoIn) -> None:
        if not await self.localidade_repo.cidade_pertence_ao_estado(
            endereco.cidade_id, endereco.estado_id
        ):
            raise HTTPException(
                status_code=400,
                detail="A cidade informada não pertence ao estado selecionado",
            )

    async def _validar_email_unico(
        self, email: str, ignorar_id: int | None = None
    ) -> None:
        existente = await self.repo.get_by_email_including_inactive(email)
        if existente is not None and (ignorar_id is None or existente.id != ignorar_id):
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    # ------------------------------------------------------------------
    # Listagem
    # ------------------------------------------------------------------
    async def listar(
        self, page: int = 1, size: int = 20, nome: str | None = None
    ) -> PaginatedResponse[UsuarioOut]:
        itens, total = await self.repo.listar_paginado(page=page, size=size, nome=nome)
        out = [self._to_out(u) for u in itens]
        return PaginatedResponse.build(out, total, page, size)

    async def obter(self, usuario_id: int) -> UsuarioOut:
        usuario = await self._carregar_model(usuario_id)
        if usuario is None or usuario.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return self._to_out(usuario)

    async def _carregar_model(self, usuario_id: int) -> Usuario | None:
        return await self.repo.get_com_relacionamentos(usuario_id)

    # ------------------------------------------------------------------
    # Criação (transacional)
    # ------------------------------------------------------------------
    async def criar(
        self, data: UsuarioCreate, criado_por: int | None = None
    ) -> UsuarioOut:
        await self._validar_email_unico(data.email)
        await self._validar_endereco(data.endereco)

        # Endereço
        from app.models.localidade import Contato as ContatoModel
        from app.models.localidade import Endereco as EnderecoModel

        endereco = EnderecoModel(**_endereco_para_orm(data.endereco))
        contato = ContatoModel(**_contato_para_orm(data.contato))

        # Funcionário
        funcionario = Funcionario(
            nome_completo=data.nome,
            endereco=endereco,
            contato=contato,
            ativo=True,
        )

        # Usuário
        usuario = Usuario(
            funcionario=funcionario,
            email=data.email,
            senha_hash=hash_password(data.senha),
            perfil=data.perfil,
            ativo=True,
        )

        try:
            await self.repo.add(usuario)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="E-mail, contato ou endereço já cadastrado",
            ) from exc

        usuario_carregado = await self._carregar_model(usuario.id)
        if usuario_carregado is None:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado após cadastro"
            )
        return self._to_out(usuario_carregado)

    # ------------------------------------------------------------------
    # Edição (transacional, em cascata)
    # ------------------------------------------------------------------
    async def atualizar(
        self, usuario_id: int, data: UsuarioUpdate, atualizado_por: int | None = None
    ) -> UsuarioOut:
        usuario = await self._carregar_model(usuario_id)
        if usuario is None or usuario.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        if data.email is not None and data.email != usuario.email:
            await self._validar_email_unico(data.email, ignorar_id=usuario_id)

        funcionario = usuario.funcionario

        if data.nome is not None:
            funcionario.nome_completo = data.nome
        if data.perfil is not None:
            usuario.perfil = data.perfil
        if data.ativo is not None:
            usuario.ativo = data.ativo
        if data.email is not None:
            usuario.email = data.email
        if data.senha is not None:
            usuario.senha_hash = hash_password(data.senha)

        if data.contato is not None:
            contato = funcionario.contato
            vals = _contato_para_orm(data.contato)
            for k, v in vals.items():
                setattr(contato, k, v)

        if data.endereco is not None:
            await self._validar_endereco(data.endereco)
            endereco = funcionario.endereco
            vals = _endereco_para_orm(data.endereco)
            for k, v in vals.items():
                setattr(endereco, k, v)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="E-mail, contato ou endereço já cadastrado",
            ) from exc

        usuario_carregado = await self._carregar_model(usuario_id)
        if usuario_carregado is None:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado após atualização"
            )
        return self._to_out(usuario_carregado)

    # ------------------------------------------------------------------
    # Exclusão (soft delete em cascata)
    # ------------------------------------------------------------------
    async def excluir(self, usuario_id: int, excluido_por: int | None = None) -> None:
        usuario = await self._carregar_model(usuario_id)
        if usuario is None or usuario.excluido_em is not None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        agora = datetime.now(UTC)
        usuario.excluido_em = agora
        usuario.excluido_por = excluido_por
        usuario.ativo = False
        usuario.funcionario.excluido_em = agora
        usuario.funcionario.excluido_por = excluido_por
        await self.session.commit()

    async def me(self, usuario_id: int) -> UsuarioOut:
        return await self.obter(usuario_id)
