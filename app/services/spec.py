from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.engine import EngineSpec
from app.infra.database.uows import (
    EngineSpecContext,
    EngineTxSpecContext,
)
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class SpecService:
    def __init__(self, uow: UnitOfWork[EngineSpecContext, EngineTxSpecContext]) -> None:
        self._uow = uow

    async def get_spec_by_engine(self, engine_id: UUID) -> EngineSpec | None:
        logger.info(f"Getting engine spec: engine_id={engine_id}")
        async with self._uow.begin(with_tx=False) as ctx:
            spec = await ctx.specs.get_engine_spec(engine_id)
            logger.info(f"Engine spec lookup finished: engine_id={engine_id} found={spec is not None}")
            return spec
