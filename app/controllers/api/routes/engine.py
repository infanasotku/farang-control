from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.container import Container
from app.controllers.api.schemas.engine import EngineSpecResponse, RegisterEngineInstanceResponse
from app.infra.logging.logger import get_logger
from app.services.engine import EngineService
from app.services.exceptions.engine import EngineNotFoundError
from app.services.exceptions.state import CurrentInstanceAliveError, InstanceDeprecatedError
from app.services.state import StateService

router = APIRouter()
logger = get_logger().getChild(__name__)


@router.get("/{engine_id}/spec")
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


@router.post("/{engine_id}/register-instance")
@inject
async def register_engine_instance(
    instance_id: Annotated[UUID, Query(...)],
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
) -> RegisterEngineInstanceResponse:
    try:
        epoch = await svc.register_instance(instance_id=instance_id, engine_id=engine_id)
    except InstanceDeprecatedError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except CurrentInstanceAliveError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EngineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return RegisterEngineInstanceResponse(epoch=epoch)
