from typing import Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Request
from sqladmin import ModelView

from app.container import Container
from app.infra.database.models.engine import Engine as EngineModel
from app.infra.database.models.engine import EngineSpec as EngineSpecModel
from app.infra.logging.logger import get_logger
from app.services.engine import EngineService

logger = get_logger().getChild(__name__)


class EngineView(ModelView, model=EngineModel):
    can_export = False

    column_list = [EngineModel.id, EngineModel.name]
    form_columns = [EngineModel.name]

    @inject
    async def update_model(
        self,
        request: Request,
        pk: str,
        data: dict,
        svc: EngineService = Provide[Container.engine_service],
    ) -> Any:
        logger.info(f"Admin updating engine: engine_id={pk}")
        await svc.update_engine(UUID(pk), data["name"])
        return EngineModel(id=pk)

    @inject
    async def insert_model(
        self,
        request: Request,
        data: dict,
        svc: EngineService = Provide[Container.engine_service],
    ) -> Any:
        logger.info(f"Admin creating engine: name={data['name']}")
        engine = await svc.create_engine(data["name"])
        logger.info(f"Admin created engine: engine_id={engine.id}")
        return EngineModel(id=engine.id)

    @inject
    async def delete_model(
        self,
        request: Request,
        pk: Any,
        svc: EngineService = Provide[Container.engine_service],
    ) -> None:
        logger.info(f"Admin deleting engine: engine_id={pk}")
        return await svc.remove_engine(UUID(pk))


class EngineSpecView(ModelView, model=EngineSpecModel):
    can_export = False
    can_create = False
    can_delete = False
    can_edit = False

    column_list = "__all__"
    form_columns = [EngineSpecModel.config, EngineSpecModel.enabled]
