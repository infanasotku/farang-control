from typing import Protocol

from dependency_injector.wiring import Provide, inject
from sqladmin import action
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.container import Container
from app.dto.projections import StartSyncAllProjectionsCmd
from app.infra.common.correlation import get_request_context
from app.infra.logging import get_logger
from app.services.projections.engine import EngineProjectionService

logger = get_logger().getChild(__name__)


class _SyncProjectionsView(Protocol):
    identity: str

    async def start_projection_sync(self, cmd: StartSyncAllProjectionsCmd) -> None: ...


class SyncProjectionsMixin:
    @action(
        name="sync_projections",
        label="Sync Projections",
        confirmation_message=(
            "Are you sure you want to sync all engine projections? "
            "This will update the status of all engines based on their actual state."
        ),
        add_in_detail=False,
        add_in_list=True,
    )
    async def start_syncing_all_projections(self: _SyncProjectionsView, request: Request) -> Response:
        logger.info("Admin syncing all engines")

        ctx = get_request_context()
        await self.start_projection_sync(StartSyncAllProjectionsCmd(correlation_id=ctx.request_id))

        return RedirectResponse(request.url_for("admin:list", identity=self.identity))

    @inject
    async def start_projection_sync(
        self,
        cmd: StartSyncAllProjectionsCmd,
        svc: EngineProjectionService = Provide[Container.projection_service],
    ) -> None:
        await svc.start_sync_all_projections(cmd)
