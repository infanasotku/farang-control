from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import (
    PgEngineSpecRepository,
    PgEngineSpecTxRepository,
)
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class EngineSpecContext(Protocol):
    specs: PgEngineSpecRepository


class EngineTxSpecContext(Protocol):
    specs: PgEngineSpecTxRepository


class PgEngineSpecContext(PgUOWContext, EngineSpecContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session)


class PgEngineSpecTxContext(PgTxUOWContext, EngineTxSpecContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecTxRepository(session)


class PgEngineSpecUnitOfWork(PgUnitOfWork[PgEngineSpecContext, PgEngineSpecTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> PgEngineSpecContext:
        return PgEngineSpecContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> PgEngineSpecTxContext:
        return PgEngineSpecTxContext(session=session, transaction=transaction)
