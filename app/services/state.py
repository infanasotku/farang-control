from uuid import UUID

from app.domains.state import LivenessStatus, ReportedPhase
from app.dto.state import CreateEngineInstance, CreateEngineRuntimeState
from app.infra.common.time import now_utc
from app.infra.database.uows.state import PgStateUnitOfWork
from app.services.exceptions.engine import EngineNotFoundError
from app.services.exceptions.state import CurrentInstanceAliveError, InstanceDeprecatedError


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

            if instance is not None:
                if state is None:
                    raise RuntimeError("Inconsistent state: instance exists but state does not exist")

                if instance.instance_id == state.current_instance_id:
                    return state.current_epoch

                raise InstanceDeprecatedError(instance_id)

            if state is not None and state.get_liveness(now_utc()) != LivenessStatus.DEAD:
                raise CurrentInstanceAliveError(state.current_instance_id)

            new_epoch = 1 if state is None else state.current_epoch + 1

            await ctx.instances.create(
                CreateEngineInstance(
                    id=instance_id,
                    engine_id=engine_id,
                    epoch=new_epoch,
                    created_at=now_utc(),
                )
            )

            new_state = CreateEngineRuntimeState(
                engine_id=engine_id,
                reported_phase=ReportedPhase.STARTING,
                observed_generation=0,
                last_seen_at=now_utc(),
                current_instance_id=instance_id,
                current_epoch=new_epoch,
                last_seq_no=0,
            )
            await ctx.states.upsert_engine_state(new_state)
            return new_epoch
