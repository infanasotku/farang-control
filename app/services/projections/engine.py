import asyncio
from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.state import DerivedEngineStatus, derive_liveness
from app.dto.projections import (
    DerivedProjection,
    StartSyncAllProjectionsCmd,
    SyncAllProjectionsCmd,
    UpsertProjection,
)
from app.infra.cache.repositories.projections import RedisEngineProjectionRepository
from app.infra.common.time import now_utc
from app.infra.database.uows.projections import ProjectionReadContext, ProjectionWriteContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class EngineProjectionService:
    def __init__(
        self, uow: UnitOfWork[ProjectionReadContext, ProjectionWriteContext], *, repo: RedisEngineProjectionRepository
    ) -> None:
        self._uow = uow
        self._repo = repo

    async def get_by_id(self, engine_id: UUID) -> DerivedProjection:
        projection = await self._repo.get_by_id(engine_id)
        if projection is None:
            raise EngineNotFoundError(engine_id)

        derived = DerivedProjection.model_validate(projection)
        if projection.last_seen_at is not None:
            derived.liveness = derive_liveness(now=now_utc(), last_seen_at=projection.last_seen_at)
        return derived

    async def get(self, *, offset: int = 0, limit: int = 100) -> list[DerivedProjection]:
        projections = await self._repo.get(offset=offset, limit=limit)

        now = now_utc()
        derived = []
        for p in projections:
            row = DerivedProjection.model_validate(p)

            if p.last_seen_at is not None:
                row.liveness = derive_liveness(now=now, last_seen_at=p.last_seen_at)

            derived.append(row)

        return derived

    async def sync_engine(self, engine_id: UUID):
        async with self._uow.begin(write=False) as ctx:
            await self._sync_engine(engine_id, ctx=ctx)

    async def _sync_engine(self, engine_id: UUID, *, ctx: ProjectionReadContext):
        logger.info(f"Syncing projection for engine: engine_id={engine_id}")

        upsert = None
        engine = await ctx.engines.get_engine_by_id(engine_id)
        if engine is None:
            logger.info(f"Projection sync found no engine, deleting projection: engine_id={engine_id}")
        else:
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

        if engine is None:
            await self._repo.delete(engine_id)
            return

        if upsert is not None:
            await self._repo.upsert(upsert)

    async def start_sync_all_projections(self, cmd: StartSyncAllProjectionsCmd):
        from app.controllers.tasks.projections import sync_all_projections_task

        logger.info("Starting sync of all engine projections")

        lock_token = await self._repo.try_lock_syncing()
        if lock_token is None:
            logger.warning("Another sync is already in progress, skipping")
            return

        sync_all_projections_task.apply_async(kwargs={"lock_token": lock_token}, task_id=cmd.correlation_id)

    async def sync_all_projections(self, cmd: SyncAllProjectionsCmd):
        logger.info("Syncing all engine projections")

        async with self._uow.begin(write=False) as ctx:
            engine_ids = await ctx.engines.get_engine_ids()

            for i in range(0, len(engine_ids), 10):
                batch = engine_ids[i : i + 10]
                await asyncio.gather(*(self._sync_engine(engine_id, ctx=ctx) for engine_id in batch))

        await self._repo.remove_extra(set(engine_ids))
        await self._repo.release_syncing_lock(cmd.lock_token)
