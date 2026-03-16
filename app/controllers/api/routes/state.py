from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.container import Container
from app.controllers.api.schemas.engine import RegisterEngineInstanceResponse
from app.controllers.api.schemas.state import HeartbeatRequest
from app.controllers.api.utils.auth import authenticate
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import (
    CurrentInstanceAliveError,
    InstanceDeprecatedError,
    InstanceNotRegisteredError,
)
from app.dto.state import ApplyHeartbeatCmd
from app.infra.logging.logger import get_logger
from app.services.state import StateService

router = APIRouter(dependencies=[Depends(authenticate)])
logger = get_logger().getChild(__name__)


@router.post("/register-instance")
@inject
async def register_engine_instance(
    instance_id: Annotated[UUID, Query(...)],
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
) -> RegisterEngineInstanceResponse:
    logger.info(f"Register instance requested: engine_id={engine_id} instance_id={instance_id}")
    try:
        epoch = await svc.register_instance(instance_id=instance_id, engine_id=engine_id)
    except InstanceDeprecatedError as e:
        logger.warning(f"Register instance rejected as deprecated: engine_id={engine_id} instance_id={instance_id}")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except CurrentInstanceAliveError as e:
        logger.warning(
            f"Register instance rejected because current owner is alive: engine_id={engine_id} instance_id={instance_id}",
            engine_id,
            instance_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EngineNotFoundError as e:
        logger.warning(
            f"Register instance failed because engine was not found: engine_id={engine_id} instance_id={instance_id}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    logger.info(f"Register instance succeeded: engine_id={engine_id} instance_id={instance_id} epoch={epoch}")
    return RegisterEngineInstanceResponse(epoch=epoch)


@router.post("/heartbeat")
@inject
async def heartbeat(
    payload: HeartbeatRequest,
    engine_id: Annotated[UUID, Path(...)],
    svc: Annotated[StateService, Depends(Provide[Container.state_service])],
):
    logger.info(
        f"Heartbeat received: engine_id={engine_id} instance_id={payload.instance_id} epoch={payload.epoch} seq_no={payload.seq_no} generation={payload.generation}"
    )
    cmd = ApplyHeartbeatCmd(
        engine_id=engine_id,
        instance_id=payload.instance_id,
        epoch=payload.epoch,
        seq_no=payload.seq_no,
        phase=payload.phase,
        generation=payload.generation,
    )
    try:
        await svc.apply_heartbeat(cmd)
    except EngineNotFoundError as e:
        logger.warning(
            f"Heartbeat failed because engine was not found: engine_id={engine_id} instance_id={payload.instance_id}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InstanceNotRegisteredError as e:
        logger.warning(
            f"Heartbeat rejected because instance is not registered: engine_id={engine_id} instance_id={payload.instance_id}"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    logger.info(f"Heartbeat processed: engine_id={engine_id} instance_id={payload.instance_id} seq_no={payload.seq_no}")
