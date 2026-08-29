from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.func.registration import decide_registration
from app.infra.common.time import now_utc
from app.infra.logging.logger import get_logger
from app.infra.postgres.uows.state import StateReadContext, StateWriteContext
from app.services.projections.engine import EngineProjectionService
from app.services.state.shared import digest_replacement_permit

logger = get_logger().getChild(__name__)


class RegisterInstanceUC:
    def __init__(
        self,
        *,
        uow: UnitOfWork[StateReadContext, StateWriteContext],
        projection: EngineProjectionService,
    ) -> None:
        self._uow = uow
        self._projection = projection

    async def run(
        self,
        *,
        instance_id: UUID,
        engine_id: UUID,
        replacement_permit: str | None = None,
    ) -> int:
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
                replacement_permit_digest=(
                    digest_replacement_permit(replacement_permit) if replacement_permit is not None else None
                ),
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

        if result.new_runtime_state is not None:
            try:
                await self._projection.sync_engine(engine_id)
            except Exception:
                logger.exception(
                    f"Failed to project engine state update on registration: engine_id={engine_id} instance_id={instance_id}"
                )

        logger.info(f"Register instance finished: engine_id={engine_id} instance_id={instance_id} epoch={result.epoch}")
        return result.epoch
