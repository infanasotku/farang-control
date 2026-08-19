import json
from typing import Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import HTTPException, Request, status
from markupsafe import Markup, escape
from sqladmin.pagination import Pagination

from app.container import Container
from app.controllers.admin.models import EngineProjection as EngineProjectionModel
from app.controllers.admin.views.base import AdminModelView, PrettyJSONField
from app.controllers.admin.views.mixins import SyncProjectionsMixin
from app.domains.exceptions.engine import EngineNotFoundError
from app.dto.spec import UpdateSpecCmd
from app.infra.logging import get_logger
from app.services.engine import EngineService
from app.services.projections.engine import EngineProjectionService
from app.services.spec import SpecService

logger = get_logger().getChild(__name__)


class EngineView(SyncProjectionsMixin, AdminModelView, model=EngineProjectionModel):
    name = "Engine"
    name_plural = "Engines"

    column_list = [
        EngineProjectionModel.engine_id,
        EngineProjectionModel.name,
        EngineProjectionModel.enabled,
        EngineProjectionModel.phase,
        EngineProjectionModel.sync,
        EngineProjectionModel.config,
        EngineProjectionModel.liveness,
    ]
    column_details_list = column_list.copy()

    form_excluded_columns = [
        EngineProjectionModel.phase,
        EngineProjectionModel.sync,
        EngineProjectionModel.liveness,
    ]
    form_overrides = {
        "config": PrettyJSONField,
    }

    @staticmethod
    def format_config(model: EngineProjectionModel, _: str) -> str:
        return Markup(f'<div style="white-space: pre-wrap;">{escape(json.dumps(model.config, indent=2))}</div>')

    column_formatters = {
        "config": lambda *_: "<COLLAPSED>",
    }
    column_formatters_detail = {EngineProjectionModel.config: format_config}

    @inject
    async def update_model(
        self,
        request: Request,
        pk: str,
        data: dict,
        engine_svc: EngineService = Provide[Container.engine_service],
        spec_svc: SpecService = Provide[Container.spec_service],
    ) -> Any:
        logger.info(f"Admin updating engine: engine_id={pk}")
        await engine_svc.update_engine(UUID(pk), data["name"])
        logger.info(f"Admin updating engine spec: engine_id={pk}")
        await spec_svc.update_spec(UpdateSpecCmd(engine_id=UUID(pk), config=data["config"], enabled=data["enabled"]))
        return EngineProjectionModel(engine_id=pk)

    @inject
    async def insert_model(
        self,
        request: Request,
        data: dict,
        engine_svc: EngineService = Provide[Container.engine_service],
        spec_svc: SpecService = Provide[Container.spec_service],
    ) -> Any:
        logger.info(f"Admin creating engine: name={data['name']}")
        engine = await engine_svc.create_engine(data["name"])
        logger.info(f"Admin creating engine spec: engine_id={engine.id}")
        await spec_svc.update_spec(UpdateSpecCmd(engine_id=engine.id, config=data["config"], enabled=data["enabled"]))
        return EngineProjectionModel(engine_id=engine.id)

    @inject
    async def delete_model(
        self,
        request: Request,
        pk: Any,
        svc: EngineService = Provide[Container.engine_service],
    ) -> None:
        logger.info(f"Admin deleting engine: engine_id={pk}")
        return await svc.remove_engine(UUID(pk))

    async def get_object_for_details(self, request: Request) -> Any:
        return await self._get_by_id(UUID(request.path_params["pk"]))

    async def get_object_for_edit(self, request: Request) -> Any:
        return await self.get_object_for_details(request)

    async def get_object_for_delete(self, value: Any) -> Any:
        return await self._get_by_id(UUID(value))

    @inject
    async def _get_by_id(
        self,
        projection_id: UUID,
        svc: EngineProjectionService = Provide[Container.projection_service],
    ) -> Any:
        try:
            projection = await svc.get_by_id(projection_id)
        except EngineNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engine not found")
        return EngineProjectionModel.from_projection(projection)

    @inject
    async def list(
        self,
        request: Request,
        svc: EngineProjectionService = Provide[Container.projection_service],
    ) -> Pagination:
        page = self.validate_page_number(request.query_params.get("page"), 1)
        page_size = self.validate_page_number(request.query_params.get("pageSize"), 0)
        page_size = min(page_size or self.page_size, max(self.page_size_options))

        projections = await svc.get(offset=(page - 1) * page_size, limit=page_size)
        rows = [EngineProjectionModel.from_projection(projection) for projection in projections]

        return Pagination(
            rows=rows,
            page=page,
            page_size=page_size,
            count=len(projections),
        )
