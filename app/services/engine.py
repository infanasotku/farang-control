from uuid import UUID

from app.domains.engine import EngineSpec
from app.infra.database.uows import PgEngineUnitOfWork


class EngineService:
    def __init__(self, uow: PgEngineUnitOfWork) -> None:
        self._uow = uow

    async def get_spec_by_engine(self, engine_id: UUID) -> EngineSpec | None:
        async with self._uow.begin(with_tx=False) as ctx:
            return await ctx.specs.get_engine_spec(engine_id)
