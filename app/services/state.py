from uuid import UUID

from app.domains.func.registration import decide_registration
from app.infra.common.time import now_utc
from app.infra.database.uows.state import PgStateUnitOfWork
from app.services.exceptions.engine import EngineNotFoundError


class StateService:
    def __init__(self, uow: PgStateUnitOfWork):
        self._uow = uow

    async def register_instance(self, *, instance_id: UUID, engine_id: UUID) -> int:
        """
        Register an engine instance in an idempotent manner and return the assigned epoch.
        """
        async with self._uow.begin(with_tx=True) as ctx:
            # Serialize registrations for the same engine,
            # including the first one when state does not exist yet.
            engine = await ctx.engines.get_engine_for_update(engine_id)
            if engine is None:
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

            if result.new_runtime_state is not None:
                await ctx.states.upsert_engine_state(result.new_runtime_state)

            return result.epoch
