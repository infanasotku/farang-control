from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import (
    PgEngineSpecRepository,
    PgEngineSpecWriteRepository,
)
from app.infra.database.uows.base import PgReadUOWContext, PgUnitOfWork, PgWriteUOWContext


class EngineSpecReadContext(Protocol):
    specs: PgEngineSpecRepository


class EngineWriteSpecContext(Protocol):
    specs: PgEngineSpecWriteRepository


class PgEngineSpecReadContext(PgReadUOWContext, EngineSpecReadContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session)


class PgEngineSpecWriteContext(PgWriteUOWContext, EngineWriteSpecContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecWriteRepository(session)


class PgEngineSpecUnitOfWork(PgUnitOfWork[PgEngineSpecReadContext, PgEngineSpecWriteContext]):
    def _make_read_ctx(self, *, session: AsyncSession) -> PgEngineSpecReadContext:
        return PgEngineSpecReadContext(session=session)

    def _make_write_ctx(
        self, *, session: AsyncSession, transaction: AsyncSessionTransaction
    ) -> PgEngineSpecWriteContext:
        return PgEngineSpecWriteContext(session=session, transaction=transaction)
