from dependency_injector.wiring import Provide, inject

from app.container import Container
from app.dto.projections import SyncAllProjectionsCmd
from app.infra.celery.task import async_task
from app.services.projections.engine import EngineProjectionService


@async_task
@inject
async def sync_all_projections_task(
    lock_token: str,
    svc: EngineProjectionService = Provide[Container.projection_service],
) -> None:
    await svc.sync_all_projections(SyncAllProjectionsCmd(lock_token=lock_token))
