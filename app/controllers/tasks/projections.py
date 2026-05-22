from celery import shared_task
from dependency_injector.wiring import Provide, inject

from app.container import Container
from app.controllers.tasks.runtime import get_runtime
from app.controllers.tasks.task import as_task
from app.dto.projections import SyncAllProjectionsCmd
from app.services.projections.engine import EngineProjectionService


@as_task
@shared_task()
def sync_all_projections_task(lock_token: str):
    runtime = get_runtime()
    runtime.run(sync_all_projections(lock_token))


@inject
async def sync_all_projections(lock_token: str, svc: EngineProjectionService = Provide[Container.projection_service]):
    await svc.sync_all_projections(SyncAllProjectionsCmd(lock_token=lock_token))
