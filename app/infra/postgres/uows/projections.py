from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.postgres.repositories.engine import PgEngineRepository, PgEngineSpecRepository
from app.infra.postgres.repositories.state import PgStateRepository
from app.infra.postgres.uows.base import PgReadUOWContext, PgUnitOfWork, PgWriteUOWContext


class ProjectionReadContext(Protocol):
    specs: PgEngineSpecRepository
    engines: PgEngineRepository
    states: PgStateRepository


class ProjectionWriteContext(Protocol):
    specs: PgEngineSpecRepository
    engines: PgEngineRepository
    states: PgStateRepository


class PgProjectionReadContext(PgReadUOWContext, ProjectionReadContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.engines = PgEngineRepository(session)
        self.specs = PgEngineSpecRepository(session)
        self.states = PgStateRepository(session)


class PgProjectionWriteContext(PgWriteUOWContext, ProjectionWriteContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.engines = PgEngineRepository(session)
        self.specs = PgEngineSpecRepository(session)
        self.states = PgStateRepository(session)


class PgProjectionUnitOfWork(PgUnitOfWork[PgProjectionReadContext, PgProjectionWriteContext]):
    def _make_read_ctx(self, *, session: AsyncSession) -> PgProjectionReadContext:
        return PgProjectionReadContext(session=session)

    def _make_write_ctx(
        self, *, session: AsyncSession, transaction: AsyncSessionTransaction
    ) -> PgProjectionWriteContext:
        return PgProjectionWriteContext(session=session, transaction=transaction)
