from fastapi import FastAPI

from app.container import Container
from app.controllers.admin import register_admin
from app.controllers.api import middlewares
from app.controllers.api import router as v1


def create_app() -> FastAPI:
    container = Container()
    container.wire(
        packages=[
            "app.controllers.api.routes",
            "app.controllers.api.utils",
        ],
        modules=[
            "app.controllers.admin.views",
            "app.controllers.admin.main",
        ],
    )
    settings = container.settings()

    app = FastAPI()

    app.include_router(v1, prefix="/api/v1")
    app.add_middleware(middlewares.CorrelationIdASGIMiddleware)

    register_admin(
        app,
        username=settings.admin.username,
        password=settings.admin.password,
        secret=settings.admin.secret,
    )

    @app.get("/healthz", include_in_schema=False)
    async def _():
        return {"status": "ok"}

    return app
