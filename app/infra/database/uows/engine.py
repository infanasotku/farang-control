from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import (
    PgEngineRepository,
    PgEngineSpecRepository,
    PgEngineSpecTxRepository,
    PgEngineTxRepository,
)
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class EngineContext(Protocol):
    specs: PgEngineSpecRepository
    engines: PgEngineRepository


class EngineTxContext(Protocol):
    specs: PgEngineSpecTxRepository
    engines: PgEngineTxRepository


class PgEngineContext(PgUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session)
        self.engines = PgEngineRepository(session)


class PgEngineTxContext(PgTxUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecTxRepository(session)
        self.engines = PgEngineTxRepository(session)


class PgEngineUnitOfWork(PgUnitOfWork[PgEngineContext, PgEngineTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> PgEngineContext:
        return PgEngineContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> PgEngineTxContext:
        return PgEngineTxContext(session=session, transaction=transaction)
