from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.engine import Engine, EngineSpec
from app.infra.database.models.engine import Engine as EngineModel
from app.infra.database.models.engine import EngineSpec as EngineSpecModel
from app.infra.database.repositories.base import PostgresRepository
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


def engine_from_model(model: EngineModel) -> Engine:
    return Engine(id=model.id, name=model.name)


class PgEngineRepository(PostgresRepository):
    async def get_engines(self) -> list[Engine]:
        logger.debug("Loading all engines")
        stmt = select(EngineModel)
        rows = await self._session.scalars(stmt)
        return [engine_from_model(row) for row in rows]

    async def get_engine_by_id(self, engine_id: UUID) -> Engine | None:
        logger.debug(f"Loading engine by id: engine_id={engine_id}")
        stmt = select(EngineModel).where(EngineModel.id == engine_id)
        row = await self._session.scalar(stmt)
        return engine_from_model(row) if row else None


class PgEngineTxRepository(PgEngineRepository):
    async def add(self, engine: Engine) -> None:
        logger.debug(f"Inserting engine: engine_id={engine.id}")
        stmt = insert(EngineModel).values(id=engine.id, name=engine.name)
        await self._session.execute(stmt)

    async def update(self, engine: Engine) -> None:
        logger.debug(f"Updating engine: engine_id={engine.id}")
        stmt = update(EngineModel).where(EngineModel.id == engine.id).values(name=engine.name)
        await self._session.execute(stmt)

    async def delete(self, engine_id: UUID) -> None:
        logger.debug(f"Deleting engine: engine_id={engine_id}")
        stmt = delete(EngineModel).where(EngineModel.id == engine_id)
        await self._session.execute(stmt)

    async def get_engine_for_update(self, engine_id: UUID) -> Engine | None:
        logger.debug(f"Loading engine for update: engine_id={engine_id}")
        stmt = select(EngineModel).where(EngineModel.id == engine_id).with_for_update()
        row = await self._session.scalar(stmt)
        return engine_from_model(row) if row else None


def engine_spec_from_model(model: EngineSpecModel) -> EngineSpec:
    return EngineSpec(
        config=model.config,
        enabled=model.enabled,
        generation=model.generation,
        engine_id=model.engine_id,
    )


class PgEngineSpecRepository(PostgresRepository):
    async def get_engine_spec(self, engine_id: UUID) -> EngineSpec | None:
        logger.debug(f"Loading engine spec: engine_id={engine_id}")
        stmt = select(EngineSpecModel).where(EngineSpecModel.engine_id == engine_id)
        row = await self._session.scalar(stmt)
        return engine_spec_from_model(row) if row else None


class PgEngineSpecTxRepository(PgEngineSpecRepository):
    async def upsert(self, create: EngineSpec) -> None:
        logger.debug(f"Upserting engine spec: engine_id={create.engine_id} generation={create.generation}")
        stmt = (
            pg_insert(EngineSpecModel)
            .values(
                config=create.config,
                enabled=create.enabled,
                generation=create.generation,
                engine_id=create.engine_id,
            )
            .on_conflict_do_update(
                index_elements=[EngineSpecModel.engine_id],
                set_={
                    "config": create.config,
                    "enabled": create.enabled,
                    "generation": create.generation,
                },
            )
        )
        await self._session.execute(stmt)

    async def delete_by_engine(self, engine_id: UUID) -> None:
        logger.debug(f"Deleting engine spec: engine_id={engine_id}")
        stmt = delete(EngineSpecModel).where(EngineSpecModel.engine_id == engine_id)
        await self._session.execute(stmt)

    async def get_engine_spec_for_update(self, engine_id: UUID) -> EngineSpec | None:
        logger.debug(f"Loading engine spec for update: engine_id={engine_id}")
        stmt = select(EngineSpecModel).where(EngineSpecModel.engine_id == engine_id).with_for_update()
        row = await self._session.scalar(stmt)
        return engine_spec_from_model(row) if row else None
