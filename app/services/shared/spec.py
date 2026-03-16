from app.domains.engine import EngineSpec
from app.infra.database.uows import EngineTxSpecContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


async def _save_event(spec: EngineSpec):
    logger.debug(f"Preparing spec outbox event: engine_id={spec.engine_id} generation={spec.generation}")
    # TODO: Implement spec diffing and event extraction logic
    # to notify engine instances about spec changes without polling.
    # This provides fast, push-based (outbox) notification of updates.
    logger.debug(f"Spec outbox event is skipped until outbox is implemented: engine_id={spec.engine_id}")
    pass


async def upsert_engine_spec(spec: EngineSpec, *, ctx: EngineTxSpecContext) -> None:
    logger.info(f"Upserting engine spec: engine_id={spec.engine_id} generation={spec.generation}")
    await ctx.specs.upsert(spec)
    logger.info(f"Engine spec persisted: engine_id={spec.engine_id} generation={spec.generation}")
    await _save_event(spec)
    logger.info(f"Engine spec side effects completed: engine_id={spec.engine_id} generation={spec.generation}")


async def remove_engine_spec(spec: EngineSpec, *, ctx: EngineTxSpecContext) -> None:
    logger.info(f"Removing engine spec: engine_id={spec.engine_id} generation={spec.generation}")
    await ctx.specs.delete_by_engine(spec.engine_id)
    logger.info(f"Engine spec removed: engine_id={spec.engine_id}")
    await _save_event(spec)
    logger.info(f"Engine spec removal side effects completed: engine_id={spec.engine_id}")
