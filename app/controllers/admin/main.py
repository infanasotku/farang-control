from pathlib import Path

from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.staticfiles import StaticFiles

from app.container import Container
from app.controllers.admin.auth import AdminAuthenticationBackend
from app.controllers.admin.views import EngineView
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)

_ADMIN_DIR = Path(__file__).parent


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
    app.mount(
        "/admin-assets",
        StaticFiles(directory=_ADMIN_DIR / "statics"),
        name="admin-assets",
    )
    authentication_backend = AdminAuthenticationBackend(secret, username=username, password=password)
    admin = Admin(
        app,
        engine,
        title="Engine panel",
        authentication_backend=authentication_backend,
        base_url="/admin",
        templates_dir=str(_ADMIN_DIR / "templates"),
    )
    admin.add_model_view(EngineView)
    logger.info("Admin panel registered with model views")
