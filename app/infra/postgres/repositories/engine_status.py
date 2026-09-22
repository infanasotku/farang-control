from uuid import UUID

from sqlalchemy import func, select

from app.dto.engine_status import EngineStatusSource
from app.infra.postgres.models.engine import Engine, EngineSpec
from app.infra.postgres.models.state import EngineRuntimeState
from app.infra.postgres.repositories.base import PostgresRepository
from app.infra.postgres.repositories.engine import engine_from_model, engine_spec_from_model
from app.infra.postgres.repositories.state import engine_runtime_state_from_model


def _source(engine: Engine, spec: EngineSpec | None, runtime: EngineRuntimeState | None) -> EngineStatusSource:
    return EngineStatusSource(
        engine=engine_from_model(engine),
        spec=engine_spec_from_model(spec) if spec is not None else None,
        runtime=engine_runtime_state_from_model(runtime) if runtime is not None else None,
    )


class PgEngineStatusRepository(PostgresRepository):
    @staticmethod
    def _query():
        # A single statement gives each status a consistent snapshot without N+1 reads.
        return (
            select(Engine, EngineSpec, EngineRuntimeState)
            .outerjoin(EngineSpec, EngineSpec.engine_id == Engine.id)
            .outerjoin(EngineRuntimeState, EngineRuntimeState.engine_id == Engine.id)
        )

    async def get_by_id(self, engine_id: UUID) -> EngineStatusSource | None:
        result = await self._session.execute(self._query().where(Engine.id == engine_id))
        row = result.one_or_none()
        return _source(*row) if row is not None else None

    async def get(self, *, offset: int = 0, limit: int = 100) -> list[EngineStatusSource]:
        result = await self._session.execute(self._query().order_by(Engine.name, Engine.id).offset(offset).limit(limit))
        return [_source(*row) for row in result]

    async def count(self) -> int:
        return await self._session.scalar(select(func.count()).select_from(Engine)) or 0
