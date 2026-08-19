from celery import shared_task
from dependency_injector.wiring import Provide, inject

from app.container import Container
from app.dto.projections import SyncAllProjectionsCmd
from app.infra.celery.runtime import get_runtime
from app.infra.celery.task import as_task
from app.services.projections.engine import EngineProjectionService


@as_task
@shared_task()
def sync_all_projections_task(lock_token: str):
    get_runtime().run(sync_all_projections(lock_token))


@inject
async def sync_all_projections(
    lock_token: str,
    svc: EngineProjectionService = Provide[Container.projection_service],
):
    await svc.sync_all_projections(SyncAllProjectionsCmd(lock_token=lock_token))
