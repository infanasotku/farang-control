from app.contracts.uow import UnitOfWork
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.func.heartbeat import apply_heartbeat
from app.dto.state import ApplyHeartbeatCmd
from app.infra.common.time import now_utc
from app.infra.logging.logger import get_logger
from app.infra.postgres.uows.state import StateReadContext, StateWriteContext
from app.services.projections.engine import EngineProjectionService

logger = get_logger().getChild(__name__)


class ApplyHeartbeatUC:
    def __init__(
        self,
        *,
        uow: UnitOfWork[StateReadContext, StateWriteContext],
        projection: EngineProjectionService,
    ) -> None:
        self._uow = uow
        self._projection = projection

    async def run(self, cmd: ApplyHeartbeatCmd) -> None:
        """
        Apply a heartbeat to an engine runtime state in an idempotent manner.

        Raises:
            EngineNotFoundError: if the specified engine does not exist.
            InstanceNotRegisteredError: if the instance is not registered (i.e., state or instance is None).
        """
        logger.info(
            f"Applying heartbeat: engine_id={cmd.engine_id} instance_id={cmd.instance_id} epoch={cmd.epoch} seq_no={cmd.seq_no} generation={cmd.generation}"
        )
        async with self._uow.begin(write=True) as ctx:
            engine = await ctx.engines.get_engine_by_id(cmd.engine_id)
            if engine is None:
                logger.warning(
                    f"Apply heartbeat failed because engine was not found: engine_id={cmd.engine_id} instance_id={cmd.instance_id}"
                )
                raise EngineNotFoundError(cmd.engine_id)

            now = now_utc()

            state = await ctx.states.get_engine_state_for_update(cmd.engine_id)
            instance = await ctx.instances.get_instance_by_id(cmd.instance_id)

            result = apply_heartbeat(
                now=now,
                instance_id=cmd.instance_id,
                state=state,
                instance=instance,
                #
                received_epoch=cmd.epoch,
                received_seq_no=cmd.seq_no,
                new_phase=cmd.phase,
                new_generation=cmd.generation,
            )

            if result.new_state is not None:
                await ctx.states.upsert_engine_state(result.new_state)

        if result.new_state is not None:
            logger.info(
                f"Heartbeat updated runtime state: engine_id={cmd.engine_id} instance_id={cmd.instance_id} seq_no={cmd.seq_no}"
            )
            try:
                await self._projection.sync_engine(cmd.engine_id)
            except Exception:
                logger.exception(
                    f"Failed to project engine state update on heartbeat: engine_id={cmd.engine_id} instance_id={cmd.instance_id} seq_no={cmd.seq_no}"
                )
        else:
            logger.info(
                f"Heartbeat produced no state changes: engine_id={cmd.engine_id} instance_id={cmd.instance_id} seq_no={cmd.seq_no}"
            )
