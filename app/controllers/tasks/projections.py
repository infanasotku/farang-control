from celery import shared_task
from dependency_injector.wiring import Provide, inject

from app.container import Container
from app.controllers.tasks.runtime import get_runtime
from app.controllers.tasks.task import as_task
from app.infra.logging import logger
from app.services.projections.engine import EngineProjectionService


@as_task
@shared_task()
def sync_all_projections_task():
    runtime = get_runtime()
    runtime.run(sync_all_projections())


@inject
async def sync_all_projections(svc: EngineProjectionService = Provide[Container.projection_service]):
    logger.info("Hello world!")
