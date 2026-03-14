from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.state import EngineInstance, EngineRuntimeState, NewEngineRuntimeState
from app.dto.state import CreateEngineInstance
from app.infra.database.models.state import EngineInstance as EngineInstanceModel
from app.infra.database.models.state import EngineRuntimeState as EngineRuntimeStateModel
from app.infra.database.repositories.base import PostgresRepository


def engine_runtime_state_from_model(model: EngineRuntimeStateModel) -> EngineRuntimeState:
    return EngineRuntimeState(
        reported_phase=model.reported_phase,
        observed_generation=model.observed_generation,
        last_seen_at=model.last_seen_at,
        engine_id=model.engine_id,
        last_seq_no=model.last_seq_no,
        #
        current_instance_id=model.current_instance_id,
        current_epoch=model.current_epoch,
    )


class PgStateRepository(PostgresRepository):
    async def get_engine_state(self, engine_id: UUID) -> EngineRuntimeState | None:
        stmt = select(EngineRuntimeStateModel).where(EngineRuntimeStateModel.engine_id == engine_id)
        row = await self._session.scalar(stmt)
        return engine_runtime_state_from_model(row) if row else None


class PgStateTxRepository(PgStateRepository):
    async def upsert_engine_state(self, state: NewEngineRuntimeState) -> None:
        stmt = (
            pg_insert(EngineRuntimeStateModel)
            .values(
                engine_id=state.engine_id,
                reported_phase=state.reported_phase,
                observed_generation=state.observed_generation,
                last_seen_at=state.last_seen_at,
                current_instance_id=state.current_instance_id,
                current_epoch=state.current_epoch,
                last_seq_no=state.last_seq_no,
            )
            .on_conflict_do_update(
                index_elements=[EngineRuntimeStateModel.engine_id],
                set_={
                    "reported_phase": state.reported_phase,
                    "observed_generation": state.observed_generation,
                    "last_seen_at": state.last_seen_at,
                    "current_instance_id": state.current_instance_id,
                    "current_epoch": state.current_epoch,
                    "last_seq_no": state.last_seq_no,
                },
            )
        )
        await self._session.execute(stmt)

    async def get_engine_state_for_update(self, engine_id: UUID) -> EngineRuntimeState | None:
        stmt = (
            select(EngineRuntimeStateModel)
            .where(
                EngineRuntimeStateModel.engine_id == engine_id,
            )
            .with_for_update()
        )
        row = await self._session.scalar(stmt)
        return engine_runtime_state_from_model(row) if row else None


def engine_instance_from_model(model: EngineInstanceModel) -> EngineInstance:
    return EngineInstance(
        instance_id=model.id,
        engine_id=model.engine_id,
        epoch=model.epoch,
        created_at=model.created_at,
    )


class PgInstanceRepository(PostgresRepository):
    async def get_instance_by_id(self, instance_id: UUID) -> EngineInstance | None:
        stmt = select(EngineInstanceModel).where(EngineInstanceModel.id == instance_id)
        row = await self._session.scalar(stmt)
        return engine_instance_from_model(row) if row else None


class PgInstanceTxRepository(PgInstanceRepository):
    async def create(self, payload: CreateEngineInstance):
        stmt = pg_insert(EngineInstanceModel).values(
            id=payload.id_,
            engine_id=payload.engine_id,
            epoch=payload.epoch,
            created_at=payload.created_at,
        )
        await self._session.execute(stmt)
