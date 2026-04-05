from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.func.heartbeat import apply_heartbeat
from app.domains.func.registration import decide_registration
from app.dto.state import ApplyHeartbeatCmd
from app.infra.common.time import now_utc
from app.infra.database.uows.state import StateReadContext, StateWriteContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class StateService:
    def __init__(self, uow: UnitOfWork[StateReadContext, StateWriteContext]) -> None:
        self._uow = uow

    async def register_instance(self, *, instance_id: UUID, engine_id: UUID) -> int:
        """
        Register an engine instance in an idempotent manner and return the assigned epoch.

        Raises:
            EngineNotFoundError: if the specified engine does not exist.
            InstanceDeprecatedError: if the requested instance ID is different from the current one but an instance with the requested ID already exists.
            CurrentInstanceAliveError: if the current instance is still alive (not DEAD) and a new instance is being requested.
        """
        logger.info(f"Registering instance: engine_id={engine_id} instance_id={instance_id}")
        async with self._uow.begin(write=True) as ctx:
            # Serialize registrations for the same engine,
            # including the first one when state does not exist yet.
            engine = await ctx.engines.get_engine_for_update(engine_id)
            if engine is None:
                logger.warning(
                    f"Register instance failed because engine was not found: engine_id={engine_id} instance_id={instance_id}"
                )
                raise EngineNotFoundError(engine_id)

            state = await ctx.states.get_engine_state_for_update(engine_id)
            instance = await ctx.instances.get_instance_by_id(instance_id)

            now = now_utc()
            result = decide_registration(
                now=now,
                engine_id=engine_id,
                requested_instance_id=instance_id,
                current_state=state,
                existing_instance=instance,
            )

            if result.new_instance is not None:
                await ctx.instances.create(result.new_instance)
                logger.info(
                    f"Instance history created: engine_id={engine_id} instance_id={instance_id} epoch={result.new_instance.epoch}"
                )

            if result.new_runtime_state is not None:
                await ctx.states.upsert_engine_state(result.new_runtime_state)
                logger.info(
                    f"Runtime state updated on registration: engine_id={engine_id} instance_id={instance_id} epoch={result.new_runtime_state.current_epoch}"
                )

            logger.info(
                f"Register instance finished: engine_id={engine_id} instance_id={instance_id} epoch={result.epoch}"
            )
            return result.epoch

    async def apply_heartbeat(self, cmd: ApplyHeartbeatCmd):
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
                logger.info(
                    f"Heartbeat updated runtime state: engine_id={cmd.engine_id} instance_id={cmd.instance_id} seq_no={cmd.seq_no}"
                )
            else:
                logger.info(
                    f"Heartbeat produced no state changes: engine_id={cmd.engine_id} instance_id={cmd.instance_id} seq_no={cmd.seq_no}"
                )
