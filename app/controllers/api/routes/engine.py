from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path

from app.container import Container
from app.controllers.api.schemas.engine import EngineSpecResponse
from app.controllers.api.utils.auth import authenticate
from app.infra.logging.logger import get_logger
from app.services.engine import EngineService

router = APIRouter(dependencies=[Depends(authenticate)])
logger = get_logger().getChild(__name__)


# TODO: Add generation and complete logic
@router.get("/spec")
@inject
async def get_engine_spec(
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[EngineService, Depends(Provide[Container.spec_service])],
) -> EngineSpecResponse:
    spec = await svc.get_by_engine(engine_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Engine spec is not found")

    logger.info(f"Engine spec is retrieved: engine_id={engine_id}")

    return EngineSpecResponse.model_validate(spec)
