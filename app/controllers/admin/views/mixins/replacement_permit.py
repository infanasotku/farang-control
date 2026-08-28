from typing import Any, Protocol
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from sqladmin import action
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.container import Container
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import EngineHasNoRuntimeStateError
from app.dto.state import ReplacementPermit
from app.infra.logging import get_logger
from app.services.state import StateService

logger = get_logger().getChild(__name__)


class _ReplacementPermitView(Protocol):
    identity: str
    templates: Any

    async def issue_engine_replacement_permit(self, engine_id: UUID) -> ReplacementPermit: ...


class ReplacementPermitMixin:
    @action(
        name="issue_replacement_permit",
        label="Issue replacement permit",
        confirmation_message=(
            "Issue a one-time replacement permit for the selected engine(s)? "
            "This will invalidate any permit that has already been issued."
        ),
        add_in_detail=True,
        add_in_list=True,
    )
    async def issue_replacement_permits(self: _ReplacementPermitView, request: Request) -> Response:
        raw_ids = [value.strip() for value in request.query_params.get("pks", "").split(",") if value.strip()]
        if not raw_ids:
            return RedirectResponse(request.url_for("admin:list", identity=self.identity))

        permits: list[ReplacementPermit] = []
        errors: list[dict[str, str]] = []
        engine_ids: list[UUID] = []
        seen_engine_ids: set[UUID] = set()

        for raw_id in raw_ids:
            try:
                engine_id = UUID(raw_id)
            except ValueError:
                errors.append({"engine_id": raw_id, "message": "Invalid engine ID"})
                continue

            if engine_id not in seen_engine_ids:
                seen_engine_ids.add(engine_id)
                engine_ids.append(engine_id)

        for engine_id in engine_ids:
            try:
                permits.append(await self.issue_engine_replacement_permit(engine_id))
            except (EngineNotFoundError, EngineHasNoRuntimeStateError) as error:
                errors.append({"engine_id": str(engine_id), "message": str(error)})

        response = await self.templates.TemplateResponse(
            request,
            "admin/replacement-permits.html",
            {
                "model_view": self,
                "permits": permits,
                "errors": errors,
                "title": "Replacement permits",
                "subtitle": "Copy newly issued permits before leaving this page",
            },
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @inject
    async def issue_engine_replacement_permit(
        self,
        engine_id: UUID,
        svc: StateService = Provide[Container.state_service],
    ) -> ReplacementPermit:
        logger.info(f"Admin issuing replacement permit: engine_id={engine_id}")
        return await svc.issue_replacement_permit(engine_id=engine_id)
