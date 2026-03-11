from fastapi import APIRouter

from app.controllers.api.routes import engine

router = APIRouter()

router.include_router(engine.router, prefix="/engines")
