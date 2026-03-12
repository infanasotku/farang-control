from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.state import (
    PgInstanceRepository,
    PgInstanceTxRepository,
    PgStateRepository,
    PgStateTxRepository,
)
from app.infra.database.uows.base import PgUnitOfWork
from app.infra.database.uows.engine import EngineContext, EngineTxContext


class StateContext(EngineContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.states = PgStateRepository(session)
        self.instances = PgInstanceRepository(session)


class StateTxContext(EngineTxContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.states = PgStateTxRepository(session)
        self.instances = PgInstanceTxRepository(session)


class PgStateUnitOfWork(PgUnitOfWork[StateContext, StateTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> StateContext:
        return StateContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> StateTxContext:
        return StateTxContext(session=session, transaction=transaction)
