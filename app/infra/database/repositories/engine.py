from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.engine import Engine
from app.domains.spec import EngineSpec
from app.infra.database.models.engine import Engine as EngineModel
from app.infra.database.models.engine import EngineSpec as EngineSpecModel
from app.infra.database.repositories.base import PostgresRepository
from app.schemas.core import CreateEngine


def engine_from_model(model: EngineModel) -> Engine:
    return Engine(id=model.id, name=model.name)


class PgEngineRepository(PostgresRepository):
    async def get_engines(self) -> list[Engine]:
        stmt = select(EngineModel)
        rows = await self._session.scalars(stmt)
        return [engine_from_model(row) for row in rows]


class PgEngineTxRepository(PgEngineRepository):
    async def add_engine(self, engine: Engine) -> None:
        stmt = insert(EngineModel).values(id=engine.id, name=engine.name)
        await self._session.execute(stmt)

    async def get_engine_for_update(self, engine_id: UUID) -> Engine | None:
        stmt = select(EngineModel).where(EngineModel.id == engine_id).with_for_update()
        row = await self._session.scalar(stmt)
        return engine_from_model(row) if row else None


def engine_spec_from_model(model: EngineSpecModel) -> EngineSpec:
    return EngineSpec(
        id=model.id,
        config=model.config,
        enabled=model.enabled,
        generation=model.generation,
        engine_id=model.engine_id,
    )


class PgEngineSpecRepository(PostgresRepository):
    async def get_engine_spec(self, engine_id: UUID) -> EngineSpec | None:
        stmt = select(EngineSpecModel).where(EngineSpecModel.engine_id == engine_id)
        row = await self._session.scalar(stmt)
        return engine_spec_from_model(row) if row else None


class PgEngineSpecTxRepository(PgEngineSpecRepository):
    async def upsert_engine_spec(self, create: CreateEngine) -> None:
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
