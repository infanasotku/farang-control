from uuid import UUID

from sqlalchemy import delete, insert, select, update

from app.dto.projections import CreateProjection, UpdateProjection
from app.infra.database.models.projections import EngineProjection
from app.infra.database.repositories.base import PostgresRepository
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class PgEngineProjectionRepository(PostgresRepository):
    async def exists(self, engine_id: UUID) -> bool:
        stmt = select(1).select_from(EngineProjection).where(EngineProjection.engine_id == engine_id)
        return bool(await self._session.scalar(stmt))


class PgEngineProjectionWriteRepository(PgEngineProjectionRepository):
    async def create(self, projection: CreateProjection) -> None:
        stmt = insert(EngineProjection).values(**projection.model_dump())
        await self._session.execute(stmt)

    async def update(self, projection: UpdateProjection) -> None:
        upsert_dict = projection.model_dump(exclude_unset=True, exclude={"engine_id"})

        stmt = update(EngineProjection).where(EngineProjection.engine_id == projection.engine_id).values(**upsert_dict)

        await self._session.execute(stmt)

    async def delete(self, engine_id: UUID) -> None:
        stmt = delete(EngineProjection).where(EngineProjection.engine_id == engine_id)
        await self._session.execute(stmt)
