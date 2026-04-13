from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.dto.projections import UpsertProjection
from app.infra.database.models.projections import EngineProjection
from app.infra.database.repositories.base import PostgresRepository
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


class PgEngineProjectionRepository(PostgresRepository):
    pass


class PgEngineProjectionWriteRepository(PgEngineProjectionRepository):
    async def upsert(self, upsert: UpsertProjection) -> None:
        upsert_dict = upsert.model_dump(exclude_unset=True, exclude={"engine_id"})

        stmt = (
            pg_insert(EngineProjection)
            .values(**upsert_dict, engine_id=upsert.engine_id)
            .on_conflict_do_update(
                index_elements=[EngineProjection.engine_id],
                set_=upsert_dict,
            )
        )

        await self._session.execute(stmt)
