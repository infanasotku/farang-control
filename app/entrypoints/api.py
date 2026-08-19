from contextlib import asynccontextmanager

from celery import Celery
from fastapi import FastAPI

from app.container import Container
from app.controllers.admin import register_admin
from app.controllers.api import middlewares
from app.controllers.api import router as v1
from app.infra.logging.logger import get_logger

logger = get_logger().getChild(__name__)


def create_app() -> FastAPI:
    logger.info("Creating API application")
    container = Container()
    container.wire(
        packages=[
            "app.controllers.admin.views",
            "app.controllers.api.routes",
            "app.controllers.api.utils",
        ],
        modules=[
            "app.controllers.admin.main",
        ],
    )
    settings = container.settings()
    read_engine = container.read_engine()
    write_engine = container.write_engine()

    Celery(
        "control-worker",
        broker=str(settings.rabbitmq.dsn),
        backend=str(settings.redis.dsn),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await container.init_resources()  # type: ignore
        try:
            yield
        finally:
            logger.info("Disposing database engines")
            await read_engine.dispose()
            await write_engine.dispose()
            await container.shutdown_resources()  # type: ignore

    app = FastAPI(lifespan=lifespan)
    app.state.container = container

    app.include_router(v1, prefix="/api/v1")
    app.add_middleware(middlewares.CorrelationIdASGIMiddleware)
    logger.info("API router and middleware configured")

    register_admin(
        app,
        username=settings.admin.username,
        password=settings.admin.password,
        secret=settings.admin.secret,
    )
    logger.info("Admin panel registered")

    @app.get("/healthz", include_in_schema=False)
    async def _():
        logger.info("Healthcheck requested")
        return {"status": "ok"}

    logger.info("API application created")
    return app
