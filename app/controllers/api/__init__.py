from fastapi import APIRouter

from app.controllers.api.routes import engine, state

router = APIRouter()

router.include_router(engine.router, prefix="/engines/{engine_id}", tags=["spec"])
router.include_router(state.router, prefix="/engines/{engine_id}", tags=["state"])
