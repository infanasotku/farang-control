from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import PgEngineRepository, PgEngineWriteRepository
from app.infra.database.repositories.state import (
    PgInstanceRepository,
    PgInstanceWriteRepository,
    PgStateRepository,
    PgStateWriteRepository,
)
from app.infra.database.uows.base import PgReadUOWContext, PgUnitOfWork, PgWriteUOWContext


class StateReadContext(Protocol):
    engines: PgEngineRepository
    states: PgStateRepository
    instances: PgInstanceRepository


class StateWriteContext(Protocol):
    engines: PgEngineWriteRepository
    states: PgStateWriteRepository
    instances: PgInstanceWriteRepository


class PgStateReadContext(PgReadUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.engines = PgEngineRepository(session)
        self.states = PgStateRepository(session)
        self.instances = PgInstanceRepository(session)


class PgStateWriteContext(PgWriteUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.engines = PgEngineWriteRepository(session)
        self.states = PgStateWriteRepository(session)
        self.instances = PgInstanceWriteRepository(session)


class PgStateUnitOfWork(PgUnitOfWork[PgStateReadContext, PgStateWriteContext]):
    def _make_read_ctx(self, *, session: AsyncSession) -> PgStateReadContext:
        return PgStateReadContext(session=session)

    def _make_write_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> PgStateWriteContext:
        return PgStateWriteContext(session=session, transaction=transaction)
