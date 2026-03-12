from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.runtime import EngineRuntimeState
from app.infra.database.models.state import EngineRuntimeState as EngineRuntimeStateModel
from app.infra.database.repositories.base import PostgresRepository


def engine_runtime_state_from_model(model: EngineRuntimeStateModel) -> EngineRuntimeState:
    return EngineRuntimeState(
        id=model.id,
        reported_phase=model.reported_phase,
        observed_generation=model.observed_generation,
        last_seen_at=model.last_seen_at,
        engine_id=model.engine_id,
    )


class PgEngineStateRepository(PostgresRepository):
    async def get_engine_state(self, engine_id: UUID) -> EngineRuntimeState | None:
        stmt = select(EngineRuntimeStateModel).where(EngineRuntimeStateModel.engine_id == engine_id)
        row = await self._session.scalar(stmt)
        return engine_runtime_state_from_model(row) if row else None


class PgEngineStateTxRepository(PgEngineStateRepository):
    async def upsert_engine_state(self, state: EngineRuntimeState) -> None:
        stmt = (
            pg_insert(EngineRuntimeStateModel)
            .values(
                reported_phase=state.reported_phase,
                observed_generation=state.observed_generation,
                last_seen_at=state.last_seen_at,
                engine_id=state.engine_id,
            )
            .on_conflict_do_update(
                index_elements=[EngineRuntimeStateModel.engine_id],
                set_={
                    "reported_phase": state.reported_phase,
                    "observed_generation": state.observed_generation,
                    "last_seen_at": state.last_seen_at,
                },
            )
        )
        await self._session.execute(stmt)
