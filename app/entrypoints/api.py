from fastapi import FastAPI

from app.container import Container
from app.controllers.api import middlewares
from app.controllers.api import router as v1


def create_app() -> FastAPI:
    container = Container()
    container.wire(
        packages=[
            "app.controllers.api.routes",
            "app.controllers.api.utils",
        ],
    )

    app = FastAPI()

    app.include_router(v1, prefix="/api/v1")
    app.add_middleware(middlewares.CorrelationIdASGIMiddleware)

    @app.get("/healthz", include_in_schema=False)
    async def _():
        return {"status": "ok"}

    return app
