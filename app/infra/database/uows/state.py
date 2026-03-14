from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import PgEngineRepository, PgEngineTxRepository
from app.infra.database.repositories.state import (
    PgInstanceRepository,
    PgInstanceTxRepository,
    PgStateRepository,
    PgStateTxRepository,
)
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class StateContext(PgUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.engines = PgEngineRepository(session)
        self.states = PgStateRepository(session)
        self.instances = PgInstanceRepository(session)


class StateTxContext(PgTxUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.engines = PgEngineTxRepository(session)
        self.states = PgStateTxRepository(session)
        self.instances = PgInstanceTxRepository(session)


class PgStateUnitOfWork(PgUnitOfWork[StateContext, StateTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> StateContext:
        return StateContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> StateTxContext:
        return StateTxContext(session=session, transaction=transaction)
