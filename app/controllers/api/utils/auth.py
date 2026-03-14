from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.container import Container
from app.infra.config.auth import AuthSettings

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Service API key",
)


@inject
async def authenticate(
    _: Request,
    api_key: Annotated[str, Security(api_key_scheme)],
    settings: Annotated[AuthSettings, Depends(Provide[Container.auth_settings])],
):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )

    if api_key != settings.edge_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
