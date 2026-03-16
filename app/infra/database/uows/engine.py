from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import (
    PgEngineRepository,
    PgEngineSpecRepository,
    PgEngineSpecTxRepository,
    PgEngineTxRepository,
)
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class EngineSpecContext(PgUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session)


class EngineSpecTxContext(PgTxUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecTxRepository(session)


class EngineContext(EngineSpecContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.engines = PgEngineRepository(session)


class EngineTxContext(EngineSpecTxContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.engines = PgEngineTxRepository(session)


class PgEngineSpecUnitOfWork(PgUnitOfWork[EngineSpecContext, EngineSpecTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> EngineSpecContext:
        return EngineSpecContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> EngineSpecTxContext:
        return EngineSpecTxContext(session=session, transaction=transaction)


class PgEngineUnitOfWork(PgUnitOfWork[EngineContext, EngineTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> EngineContext:
        return EngineContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> EngineTxContext:
        return EngineTxContext(session=session, transaction=transaction)
