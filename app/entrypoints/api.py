from fastapi import FastAPI

from app.container import Container
from app.controllers import api as api_v1


def create_app() -> FastAPI:
    container = Container()
    container.wire(
        packages=[
            "app.controllers.api.routes",
        ],
    )

    app = FastAPI()

    app.include_router(api_v1.router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok"}
