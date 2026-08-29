from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.container import Container
from app.controllers.api.schemas.state import ReplacementPermitResponse
from app.controllers.api.utils.auth import authenticate_operator
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import EngineHasNoRuntimeStateError
from app.infra.logging.logger import get_logger
from app.services.state import StateService

router = APIRouter(dependencies=[Depends(authenticate_operator)])
logger = get_logger().getChild(__name__)


@router.post("/replacement-permit", status_code=status.HTTP_201_CREATED)
@inject
async def issue_replacement_permit(
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
) -> ReplacementPermitResponse:
    logger.info(f"Replacement permit requested: engine_id={engine_id}")
    try:
        permit = await svc.issue_replacement_permit(engine_id=engine_id)
    except EngineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EngineHasNoRuntimeStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ReplacementPermitResponse.model_validate(permit.model_dump())


@router.delete("/replacement-permit", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def revoke_replacement_permit(
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
) -> Response:
    logger.info(f"Replacement permit revocation requested: engine_id={engine_id}")
    try:
        await svc.revoke_replacement_permit(engine_id=engine_id)
    except EngineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EngineHasNoRuntimeStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
