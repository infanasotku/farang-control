from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.state import DerivedEngineStatus
from app.dto.projections import UpsertProjection
from app.infra.common.time import now_utc
from app.infra.database.uows.projections import ProjectionReadContext, ProjectionWriteContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class EngineProjectionService:
    def __init__(self, uow: UnitOfWork[ProjectionReadContext, ProjectionWriteContext]) -> None:
        self._uow = uow

    async def sync_engine(self, engine_id: UUID):
        logger.info(f"Syncing projection for engine: engine_id={engine_id}")
        async with self._uow.begin(write=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(engine_id)
            if engine is None:
                logger.info(f"Projection sync found no engine, deleting projection: engine_id={engine_id}")
                await ctx.projections.delete(engine_id)
                return

            spec = await ctx.specs.get_engine_spec(engine_id)
            if spec is None:
                logger.info(f"Projection sync found no spec for engine, using defaults: engine_id={engine_id}")

            state = await ctx.states.get_engine_state(engine_id)
            if state is None:
                logger.info(f"Projection sync found no state for engine, using defaults: engine_id={engine_id}")

            upsert = UpsertProjection(
                engine_id=engine.id,
                name=engine.name,
                config=spec.config if spec else {},
                enabled=spec.enabled if spec else False,
                phase=state.reported_phase if state else None,
                last_seen_at=state.last_seen_at if state else None,
                sync=DerivedEngineStatus.derive(now_utc(), spec=spec, runtime=state).sync if state and spec else None,
            )

            await ctx.projections.upsert(upsert)
