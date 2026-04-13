from typing import Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Request
from sqladmin import ModelView

from app.container import Container
from app.dto.spec import UpdateSpecCmd
from app.infra.database.models.projections import EngineProjection as EngineProjectionModel
from app.infra.logging.logger import get_logger
from app.services.engine import EngineService
from app.services.spec import SpecService

logger = get_logger().getChild(__name__)


class EngineView(ModelView, model=EngineProjectionModel):
    can_export = False
    column_list = "__all__"

    column_formatters = {
        "config": lambda *_: "<COLLAPSED>",
    }

    form_excluded_columns = [EngineProjectionModel.phase]

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
