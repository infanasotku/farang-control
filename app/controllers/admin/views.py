from typing import Any, Tuple

from fastapi import Request
from sqladmin import ModelView

from app.infra.database.models.engine import Engine as EngineModel


class EngineView(ModelView, model=EngineModel):
    can_export = True

    column_list = [EngineModel.id, EngineModel.name]

    async def update_model(self, request: Request, pk: str, data: dict) -> Any:
        return super().update_model(request, pk, data)

    async def insert_model(self, request: Request, data: dict) -> Any:
        return await super().insert_model(request, data)

    async def delete_model(self, request: Request, pk: Any) -> None:
        return await super().delete_model(request, pk)

    async def get_list_value(self, obj: Any, prop: str) -> Tuple[Any, Any]:
        return await super().get_list_value(obj, prop)

    async def get_detail_value(self, obj: Any, prop: str) -> Tuple[Any, Any]:
        return await super().get_detail_value(obj, prop)
