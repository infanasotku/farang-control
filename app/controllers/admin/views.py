import json
from typing import Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Request
from markupsafe import Markup, escape
from sqladmin import ModelView
from sqladmin.fields import JSONField
from wtforms.widgets import TextArea

from app.container import Container
from app.dto.spec import UpdateSpecCmd
from app.infra.database.models.projections import EngineProjection as EngineProjectionModel
from app.infra.logging.logger import get_logger
from app.services.engine import EngineService
from app.services.spec import SpecService

logger = get_logger().getChild(__name__)


class LargeTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("rows", 24)
        kwargs.setdefault("style", "font-family: monospace;")
        return super().__call__(field, **kwargs)


class ConfigJSONField(JSONField):
    widget = LargeTextAreaWidget()

    def _value(self) -> str:
        data = {}

        if self.raw_data:
            data = json.loads(self.raw_data[0])

        if self.data:
            data = self.data

        return json.dumps(data, ensure_ascii=False, indent=2)


class EngineView(ModelView, model=EngineProjectionModel):
    name = "Engine"
    name_plural = "Engines"

    can_export = False
    column_list = "__all__"

    form_excluded_columns = [EngineProjectionModel.phase]
    form_overrides = {
        "config": ConfigJSONField,
    }

    @staticmethod
    def format_config(m, _) -> str:
        return Markup(f'<div style="white-space: pre-wrap;">{escape(json.dumps(m.config, indent=2))}</div>')

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
