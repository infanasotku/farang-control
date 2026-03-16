from uuid import UUID

from app.domains.engine import Engine, EngineSpec
from app.infra.database.uows import PgEngineUnitOfWork
from app.services.exceptions.engine import EngineNotFoundError


class EngineService:
    def __init__(self, uow: PgEngineUnitOfWork) -> None:
        self._uow = uow

    async def update_engine(self, engine_id: UUID, name: str) -> EngineSpec | None:
        async with self._uow.begin(with_tx=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(engine_id)
            if engine is None:
                raise EngineNotFoundError(engine_id)

            engine.name = name
            await ctx.engines.update(engine)

            return await ctx.specs.get_engine_spec(engine_id)

    async def create_engine(self, name: str) -> Engine:
        async with self._uow.begin(with_tx=True) as ctx:
            engine = Engine.create(name)
            await ctx.engines.add(engine)

            spec = EngineSpec.initial(engine.id)
            await ctx.specs.upsert_engine_spec(spec)
            return engine

    async def get_spec_by_engine(self, engine_id: UUID) -> EngineSpec | None:
        async with self._uow.begin(with_tx=False) as ctx:
            return await ctx.specs.get_engine_spec(engine_id)
