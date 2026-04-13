from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine

from app.container import Container
from app.controllers.admin.auth import AdminAuthenticationBackend
from app.controllers.admin.views import EngineView
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


@inject
def register_admin(
    app: FastAPI,
    *,
    username: str,
    password: str,
    secret: str,
    engine: AsyncEngine = Provide[Container.read_engine],
):
    logger.info("Registering admin panel")
    authentication_backend = AdminAuthenticationBackend(secret, username=username, password=password)
    admin = Admin(
        app,
        engine,
        title="Engine panel",
        authentication_backend=authentication_backend,
        base_url="/admin",
    )
    admin.add_model_view(EngineView)
    logger.info("Admin panel registered with model views")
