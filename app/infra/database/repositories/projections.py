from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.dto.projections import UpsertProjection
from app.infra.database.models.projections import EngineProjection
from app.infra.database.repositories.base import PostgresRepository
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class PgEngineProjectionRepository(PostgresRepository):
    pass


class PgEngineProjectionWriteRepository(PgEngineProjectionRepository):
    async def delete(self, engine_id: UUID) -> None:
        stmt = delete(EngineProjection).where(EngineProjection.engine_id == engine_id)
        await self._session.execute(stmt)

    async def upsert(self, projection: UpsertProjection) -> None:
        data = projection.model_dump(exclude={"engine_id"})

        stmt = (
            pg_insert(EngineProjection)
            .values(**data, engine_id=projection.engine_id)
            .on_conflict_do_update(index_elements=[EngineProjection.engine_id], set_=data)
        )
        await self._session.execute(stmt)
