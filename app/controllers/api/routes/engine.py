from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.container import Container
from app.controllers.api.schemas.engine import EngineSpecResponse, RegisterEngineInstanceResponse
from app.infra.logging.logger import get_logger
from app.services.spec import SpecService
from app.services.state import StateService

router = APIRouter()
logger = get_logger().getChild(__name__)


@router.get("/{engine_id}/spec")
@inject
async def get_engine_spec(
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[SpecService, Depends(Provide[Container.spec_service])],
) -> EngineSpecResponse:
    spec = await svc.get_by_engine(engine_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Engine spec is not found")

    logger.info(f"Engine spec is retrieved: engine_id={engine_id}")

    return EngineSpecResponse.model_validate(spec)


@router.post("/{engine_id}/register-instance")
@inject
async def register_engine_instance(
    instance_id: Annotated[UUID, Query(...)],
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
) -> RegisterEngineInstanceResponse:
    pass
