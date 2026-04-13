from app.contracts.uow import UnitOfWork
from app.domains.engine import Engine
from app.domains.state import InstancePhase
from app.dto.projections import UpsertProjection
from app.infra.database.uows.projections import ProjectionReadContext, ProjectionWriteContext


class EngineProjectionService:
    def __init__(self, uow: UnitOfWork[ProjectionReadContext, ProjectionWriteContext]) -> None:
        self._uow = uow

    async def on_engine_created(self, engine: Engine):
        update = UpsertProjection(
            engine_id=engine.id,
            name=engine.name,
            config={},
            enabled=False,
            phase=InstancePhase.UNKNOWN,
        )

        async with self._uow.begin(write=True) as ctx:
            await ctx.projections.upsert(update)
