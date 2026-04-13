from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.projections import PgEngineProjectionRepository, PgEngineProjectionWriteRepository
from app.infra.database.uows.base import PgReadUOWContext, PgUnitOfWork, PgWriteUOWContext


class ProjectionReadContext(Protocol):
    projections: PgEngineProjectionRepository


class ProjectionWriteContext(Protocol):
    projections: PgEngineProjectionWriteRepository


class PgProjectionReadContext(PgReadUOWContext, ProjectionReadContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.projections = PgEngineProjectionRepository(session)


class PgProjectionWriteContext(PgWriteUOWContext, ProjectionWriteContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.projections = PgEngineProjectionWriteRepository(session)


class PgProjectionUnitOfWork(PgUnitOfWork[PgProjectionReadContext, PgProjectionWriteContext]):
    def _make_read_ctx(self, *, session: AsyncSession) -> PgProjectionReadContext:
        return PgProjectionReadContext(session=session)

    def _make_write_ctx(
        self, *, session: AsyncSession, transaction: AsyncSessionTransaction
    ) -> PgProjectionWriteContext:
        return PgProjectionWriteContext(session=session, transaction=transaction)
