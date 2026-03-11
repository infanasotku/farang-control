from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path

from app.container import Container
from app.controllers.api.schemas.engine import EngineSpecResponse
from app.services.spec import SpecService

router = APIRouter()


@router.get("/{engine_id}/spec")
@inject
async def get_engine_spec(
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[SpecService, Depends(Provide[Container.spec_service])],
) -> EngineSpecResponse:
    spec = await svc.get_by_engine(engine_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Engine spec is not found")

    return EngineSpecResponse.model_validate(spec)
