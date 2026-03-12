from uuid import UUID

from app.domains.runtime import NewEngineRuntimeState, ReportedPhase
from app.infra.common.time import now_utc
from app.infra.database.uows.state import PgStateUnitOfWork
from app.schemas.state import CreateEngineInstance
from app.services.exceptions.state import InstanceAliveError, InstanceDeprecatedError


class StateService:
    def __init__(self, uow: PgStateUnitOfWork):
        self._uow = uow

    async def register_instance(self, *, instance_id: UUID, engine_id: UUID) -> int:
        async with self._uow.begin(with_tx=True) as ctx:
            state = await ctx.states.get_engine_state_for_update(engine_id)
            instance = await ctx.instances.get_instance_by_id(instance_id)
            if instance is not None:
                # Should not happen because instance is created after state is created, but just in case
                if state is None:
                    raise RuntimeError("Inconsistent state: instance exists but state does not exist")

                if instance.id_ == state.current_instance_id:
                    if state.current_epoch is None:
                        raise RuntimeError("Inconsistent state: instance exists but current_epoch is None")
                    return state.current_epoch

                raise InstanceDeprecatedError(instance_id)

            if state is not None:
                if state.get_liveness() == "alive":
                    raise InstanceAliveError(state.current_instance_id)

            new_epoch = 1 if state is None else state.current_epoch + 1
            phase = ReportedPhase.STARTING

            await ctx.instances.create(
                CreateEngineInstance(
                    id=instance_id,
                    engine_id=engine_id,
                    epoch=new_epoch,
                )
            )

            new_state = NewEngineRuntimeState(
                engine_id=engine_id,
                reported_phase=phase,
                observed_generation=0,
                last_seen_at=now_utc(),
                current_instance_id=instance_id,
                current_epoch=new_epoch,
                last_seq_no=0,
            )
            await ctx.states.upsert_engine_state(new_state)
            return new_epoch
