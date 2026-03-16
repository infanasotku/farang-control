from app.domains.engine import EngineSpec
from app.infra.database.uows import EngineSpecTxContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


async def save_event(spec: EngineSpec):
    logger.debug(f"Saving events from spec: engine_id={spec.engine_id}")
    # TODO: Implement spec diffing and event extraction logic
    # to notify engine instances about spec changes without polling.
    # This provides fast, push-based notification of updates.
    pass


async def upsert_engine_spec(spec: EngineSpec, *, ctx: EngineSpecTxContext) -> None:
    logger.info(f"Upserting engine spec: engine_id={spec.engine_id} generation={spec.generation}")
    await ctx.specs.upsert(spec)
    await save_event(spec)


async def remove_engine_spec(spec: EngineSpec, *, ctx: EngineSpecTxContext) -> None:
    logger.info(f"Removing engine spec: engine_id={spec.engine_id}")
    await ctx.specs.delete_by_engine(spec.engine_id)
    await save_event(spec)
