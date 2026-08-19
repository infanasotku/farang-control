from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.postgres.repositories.engine import (
    PgEngineRepository,
    PgEngineSpecRepository,
    PgEngineSpecWriteRepository,
    PgEngineWriteRepository,
)
from app.infra.postgres.uows.base import PgReadUOWContext, PgUnitOfWork, PgWriteUOWContext


class EngineReadContext(Protocol):
    specs: PgEngineSpecRepository
    engines: PgEngineRepository


class EngineWriteContext(Protocol):
    specs: PgEngineSpecWriteRepository
    engines: PgEngineWriteRepository


class PgEngineReadContext(PgReadUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session)
        self.engines = PgEngineRepository(session)


class PgEngineWriteContext(PgWriteUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecWriteRepository(session)
        self.engines = PgEngineWriteRepository(session)


class PgEngineUnitOfWork(PgUnitOfWork[PgEngineReadContext, PgEngineWriteContext]):
    def _make_read_ctx(self, *, session: AsyncSession) -> PgEngineReadContext:
        return PgEngineReadContext(session=session)

    def _make_write_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> PgEngineWriteContext:
        return PgEngineWriteContext(session=session, transaction=transaction)
