from uuid import UUID

from app.domains.spec import EngineSpec
from app.infra.database.uows import PgSpecUnitOfWork


class EngineService:
    def __init__(self, uow: PgSpecUnitOfWork) -> None:
        self._uow = uow

    async def get_by_engine(self, engine_id: UUID) -> EngineSpec | None:
        async with self._uow.begin(with_tx=False) as ctx:
            return await ctx.specs.get_engine_spec(engine_id)
