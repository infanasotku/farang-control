from typing import Any, Tuple
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Request
from sqladmin import ModelView

from app.container import Container
from app.infra.database.models.engine import Engine as EngineModel
from app.services.engine import EngineService


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
        await svc.update_engine(UUID(pk), data["name"])
        return EngineModel(id=pk)

    @inject
    async def insert_model(
        self,
        request: Request,
        data: dict,
        svc: EngineService = Provide[Container.engine_service],
    ) -> Any:
        engine = await svc.create_engine(data["name"])
        return EngineModel(id=engine.id)

    async def delete_model(self, request: Request, pk: Any) -> None:
        return await super().delete_model(request, pk)

    async def get_detail_value(self, obj: Any, prop: str) -> Tuple[Any, Any]:
        return await super().get_detail_value(obj, prop)
