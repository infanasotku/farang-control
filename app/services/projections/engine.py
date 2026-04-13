from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.engine import Engine
from app.domains.state import InstancePhase
from app.dto.projections import CreateProjection, UpdateProjection
from app.infra.database.uows.projections import ProjectionReadContext, ProjectionWriteContext
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


def _create_initial_projection(engine: Engine) -> CreateProjection:
    return CreateProjection(
        engine_id=engine.id,
        name=engine.name,
        config={},
        enabled=False,
        phase=InstancePhase.UNKNOWN,
    )


class EngineProjectionService:
    def __init__(self, uow: UnitOfWork[ProjectionReadContext, ProjectionWriteContext]) -> None:
        self._uow = uow

    async def on_engine_created(self, engine: Engine):
        create = _create_initial_projection(engine)

        async with self._uow.begin(write=True) as ctx:
            await ctx.projections.create(create)

    async def on_engine_updated(self, engine: Engine):
        update = UpdateProjection(
            engine_id=engine.id,
            name=engine.name,
        )

        async with self._uow.begin(write=True) as ctx:
            if not await ctx.projections.exists(engine.id):
                create = _create_initial_projection(engine)
                await ctx.projections.create(create)
            else:
                await ctx.projections.update(update)

    async def on_engine_removed(self, engine_id: UUID):
        async with self._uow.begin(write=True) as ctx:
            await ctx.projections.delete(engine_id)
