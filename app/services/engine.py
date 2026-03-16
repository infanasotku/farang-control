from uuid import UUID

from app.domains.engine import Engine, EngineSpec
from app.infra.database.uows import PgEngineUnitOfWork
from app.infra.logging.logger import get_logger
from app.services.exceptions.engine import EngineNotFoundError, EngineSpecNotFoundError
from app.services.helpers.spec import remove_engine_spec, upsert_engine_spec

logger = get_logger().getChild(__name__)


class EngineService:
    def __init__(self, uow: PgEngineUnitOfWork) -> None:
        self._uow = uow

    async def update_engine(self, engine_id: UUID, name: str) -> Engine:
        logger.info(f"Updating engine: engine_id={engine_id}")
        async with self._uow.begin(with_tx=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(engine_id)
            if engine is None:
                logger.warning(f"Update engine failed because engine was not found: engine_id={engine_id}")
                raise EngineNotFoundError(engine_id)

            engine.name = name
            await ctx.engines.update(engine)
            logger.info(f"Engine updated: engine_id={engine_id}")
            return engine

    async def create_engine(self, name: str) -> Engine:
        logger.info(f"Creating engine: name={name}")
        async with self._uow.begin(with_tx=True) as ctx:
            engine = Engine.create(name)
            await ctx.engines.add(engine)

            spec = EngineSpec.initial(engine.id)
            await upsert_engine_spec(spec, ctx=ctx)
            logger.info(f"Engine created with initial spec: engine_id={engine.id}")
            return engine

    async def remove_engine(self, engine_id: UUID) -> None:
        logger.info(f"Removing engine: engine_id={engine_id}")
        async with self._uow.begin(with_tx=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(engine_id)
            if engine is None:
                logger.warning(f"Remove engine failed because engine was not found: engine_id={engine_id}")
                raise EngineNotFoundError(engine_id)

            spec = await ctx.specs.get_engine_spec(engine_id)
            if spec is None:
                raise EngineSpecNotFoundError(engine_id)
            await remove_engine_spec(spec, ctx=ctx)

            await ctx.engines.delete(engine_id)
            logger.info(f"Engine removed: engine_id={engine_id}")
