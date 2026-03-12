from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.database.repositories.engine import PgEngineSpecRepository, PgEngineSpecTxRepository
from app.infra.database.uows.base import PgTxUOWContext, PgUnitOfWork, PgUOWContext


class SpecContext(PgUOWContext):
    def __init__(self, *, session: AsyncSession):
        super().__init__(session=session)
        self.specs = PgEngineSpecRepository(session=session)


class SpecTxContext(PgTxUOWContext):
    def __init__(self, *, session: AsyncSession, transaction: AsyncSessionTransaction):
        super().__init__(session=session, transaction=transaction)
        self.specs = PgEngineSpecTxRepository(session=session)


class PgSpecUnitOfWork(PgUnitOfWork[SpecContext, SpecTxContext]):
    def _make_plain_ctx(self, *, session: AsyncSession) -> SpecContext:
        return SpecContext(session=session)

    def _make_tx_ctx(self, *, session: AsyncSession, transaction: AsyncSessionTransaction) -> SpecTxContext:
        return SpecTxContext(session=session, transaction=transaction)
