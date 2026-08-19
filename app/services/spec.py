from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.engine import EngineSpec
from app.domains.exceptions.engine import EngineSpecNotFoundError
from app.dto.spec import UpdateSpecCmd
from app.infra.logging.logger import get_logger
from app.infra.postgres.uows import (
    EngineSpecReadContext,
    EngineWriteSpecContext,
)
from app.services.projections.engine import EngineProjectionService
from app.services.shared.spec import upsert_engine_spec

logger = get_logger().getChild(__name__)


class SpecService:
    def __init__(
        self, uow: UnitOfWork[EngineSpecReadContext, EngineWriteSpecContext], *, projection: EngineProjectionService
    ) -> None:
        self._uow = uow
        self._projection = projection

    async def get_spec_by_engine(self, engine_id: UUID) -> EngineSpec | None:
        logger.info(f"Getting engine spec: engine_id={engine_id}")
        async with self._uow.begin(write=False) as ctx:
            spec = await ctx.specs.get_engine_spec(engine_id)
            logger.info(f"Engine spec lookup finished: engine_id={engine_id} found={spec is not None}")
            return spec

    async def update_spec(self, cmd: UpdateSpecCmd):
        logger.info(f"Updating engine spec: engine_id={cmd.engine_id}")
        async with self._uow.begin(write=True) as ctx:
            spec = await ctx.specs.get_engine_spec_for_update(cmd.engine_id)
            if spec is None:
                logger.warning(f"Update engine spec failed because spec was not found: engine_id={cmd.engine_id}")
                raise EngineSpecNotFoundError(cmd.engine_id)

            previous_generation = spec.generation
            spec.update(config=cmd.config, enabled=cmd.enabled)
            logger.info(
                f"Engine spec update prepared: engine_id={cmd.engine_id} changed={spec.generation != previous_generation} previous_generation={previous_generation} next_generation={spec.generation}"
            )
            await upsert_engine_spec(spec, ctx=ctx)

        try:
            await self._projection.sync_engine(spec.engine_id)
        except Exception:
            logger.exception(f"Failed to project engine spec update: engine_id={cmd.engine_id}")

        logger.info(f"Engine spec updated: engine_id={cmd.engine_id} generation={spec.generation}")
