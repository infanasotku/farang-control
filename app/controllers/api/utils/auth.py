from hmac import compare_digest
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.container import Container
from app.infra.config.auth import AuthSettings
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Service API key",
)

operator_api_key_scheme = APIKeyHeader(
    name="X-Operator-Key",
    scheme_name="OperatorApiKeyAuth",
    description="Operator API key",
    auto_error=False,
)


@inject
async def authenticate(
    _: Request,
    api_key: Annotated[str, Security(api_key_scheme)],
    settings: Annotated[AuthSettings, Depends(Provide[Container.auth_settings])],
):
    if not api_key:
        logger.warning("API authentication failed: missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )

    if not compare_digest(api_key, settings.edge_api_key):
        logger.warning("API authentication failed: invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    logger.info("API authentication succeeded")


@inject
async def authenticate_operator(
    _: Request,
    api_key: Annotated[str | None, Security(operator_api_key_scheme)],
    settings: Annotated[AuthSettings, Depends(Provide[Container.auth_settings])],
):
    validate_operator_api_key(api_key, settings)
    logger.info("Operator API authentication succeeded")


def validate_operator_api_key(api_key: str | None, settings: AuthSettings) -> None:
    if not settings.operator_api_key:
        logger.error("Operator API authentication is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operator API is not configured",
        )

    if not api_key:
        logger.warning("Operator API authentication failed: missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator API key is missing",
        )

    if not compare_digest(api_key, settings.operator_api_key):
        logger.warning("Operator API authentication failed: invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid operator API key",
        )
