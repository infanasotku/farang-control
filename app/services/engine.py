from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.engine import Engine
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.func import engine as engine_func
from app.dto.engine_status import EngineStatus, EngineStatusPage
from app.infra.common.time import now_utc
from app.infra.logging.logger import get_logger
from app.infra.postgres.uows import EngineReadContext, EngineWriteContext
from app.services.shared.spec import remove_engine_spec, upsert_engine_spec

logger = get_logger().getChild(__name__)


class EngineService:
    def __init__(self, uow: UnitOfWork[EngineReadContext, EngineWriteContext]) -> None:
        self._uow = uow

    async def get_status(self, engine_id: UUID) -> EngineStatus:
        async with self._uow.begin(write=False) as ctx:
            source = await ctx.statuses.get_by_id(engine_id)
        if source is None:
            raise EngineNotFoundError(engine_id)
        return EngineStatus.derive(source, now=now_utc())

    async def get_statuses(self, *, offset: int = 0, limit: int = 100) -> EngineStatusPage:
        async with self._uow.begin(write=False) as ctx:
            sources = await ctx.statuses.get(offset=offset, limit=limit)
            total = await ctx.statuses.count()
        now = now_utc()
        return EngineStatusPage(items=[EngineStatus.derive(source, now=now) for source in sources], total=total)

    async def update_engine(self, engine_id: UUID, name: str) -> Engine:
        logger.info(f"Updating engine: engine_id={engine_id}")
        async with self._uow.begin(write=True) as ctx:
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
        async with self._uow.begin(write=True) as ctx:
            creation_result = engine_func.create_engine(name)

            await ctx.engines.add(creation_result.engine)
            await upsert_engine_spec(creation_result.spec, ctx=ctx)

        logger.info(f"Engine created with initial spec: engine_id={creation_result.engine.id}")
        return creation_result.engine

    async def remove_engine(self, engine_id: UUID) -> None:
        logger.info(f"Removing engine: engine_id={engine_id}")
        async with self._uow.begin(write=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(engine_id)
            spec = await ctx.specs.get_engine_spec(engine_id)

            removal_result = engine_func.remove_engine(
                engine_id=engine_id,
                engine=engine,
                spec=spec,
            )

            if removal_result.engine_to_remove is not None:
                await ctx.engines.delete(engine_id)
            if removal_result.spec_to_remove is not None:
                await remove_engine_spec(removal_result.spec_to_remove, ctx=ctx)
            else:
                logger.info(f"Engine has no spec to remove: engine_id={engine_id}")

        logger.info(f"Engine removed: engine_id={engine_id}")
