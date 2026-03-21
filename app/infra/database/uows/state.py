from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import PgEngineRepository, PgEngineTxRepository
from app.infra.database.repositories.state import (
    PgInstanceRepository,
    PgInstanceTxRepository,
    PgStateRepository,
    PgStateTxRepository,
)
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class StateContext(Protocol):
    engines: PgEngineRepository
    states: PgStateRepository
    instances: PgInstanceRepository


class StateTxContext(Protocol):
    engines: PgEngineTxRepository
    states: PgStateTxRepository
    instances: PgInstanceTxRepository


class PgStateContext(PgUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.engines = PgEngineRepository(session)
        self.states = PgStateRepository(session)
        self.instances = PgInstanceRepository(session)


class PgStateTxContext(PgTxUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.engines = PgEngineTxRepository(session)
        self.states = PgStateTxRepository(session)
        self.instances = PgInstanceTxRepository(session)


class PgStateUnitOfWork(PgUnitOfWork[PgStateContext, PgStateTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> PgStateContext:
        return PgStateContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> PgStateTxContext:
        return PgStateTxContext(session=session, transaction=transaction)
