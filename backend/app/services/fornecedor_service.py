"""Service transacional do CRUD de fornecedores."""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fornecedor import Fornecedor
from app.models.localidade import Contato, Endereco
from app.repositories.fornecedor_repository import FornecedorRepository
from app.services.localidade_service import LocalidadeService
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate


class FornecedorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FornecedorRepository(session)
        self.localidade_service = LocalidadeService(session)

    async def _validar_endereco(self, cidade_id: int, estado_id: int) -> None:
        await self.localidade_service.validar_cidade_pertence_ao_estado(
            cidade_id, estado_id
        )

    @staticmethod
    def _to_out(fornecedor: Fornecedor) -> FornecedorOut:
        return FornecedorOut.model_validate(fornecedor, from_attributes=True)

    async def listar(self) -> list[FornecedorOut]:
        return [self._to_out(item) for item in await self.repo.listar()]

    async def obter(self, fornecedor_id: int) -> FornecedorOut:
        fornecedor = await self.repo.obter(fornecedor_id)
        if fornecedor is None:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
        return self._to_out(fornecedor)

    async def criar(self, data: FornecedorCreate) -> FornecedorOut:
        await self._validar_endereco(data.endereco.cidade_id, data.endereco.estado_id)
        fornecedor = Fornecedor(
            nome_empresa=data.nome_empresa,
            contato=Contato(**data.contato.model_dump()),
            endereco=Endereco(**data.endereco.model_dump(exclude={"estado_id"})),
            ativo=data.ativo,
        )
        try:
            await self.repo.add(fornecedor)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Fornecedor, contato ou endereço já cadastrado",
            ) from exc
        return await self.obter(fornecedor.id)

    async def atualizar(
        self, fornecedor_id: int, data: FornecedorUpdate
    ) -> FornecedorOut:
        fornecedor = await self.repo.obter(fornecedor_id)
        if fornecedor is None:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
        if data.nome_empresa is not None:
            fornecedor.nome_empresa = data.nome_empresa
        if data.ativo is not None:
            fornecedor.ativo = data.ativo
        if data.contato is not None:
            for campo, valor in data.contato.model_dump().items():
                setattr(fornecedor.contato, campo, valor)
        if data.endereco is not None:
            await self._validar_endereco(
                data.endereco.cidade_id, data.endereco.estado_id
            )
            for campo, valor in data.endereco.model_dump(exclude={"estado_id"}).items():
                setattr(fornecedor.endereco, campo, valor)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Fornecedor, contato ou endereço já cadastrado",
            ) from exc
        return await self.obter(fornecedor_id)

    async def excluir(self, fornecedor_id: int, excluido_por: int | None) -> None:
        fornecedor = await self.repo.obter(fornecedor_id)
        if fornecedor is None:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
        fornecedor.ativo = False
        await self.repo.soft_delete(fornecedor_id, excluido_por)
        await self.session.commit()
