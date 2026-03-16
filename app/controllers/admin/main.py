from dependency_injector.wiring import inject
from fastapi import FastAPI
from sqladmin import Admin

from app.controllers.admin.auth import AdminAuthenticationBackend
from app.controllers.admin.views import EngineView


@inject
def register_admin(
    app: FastAPI,
    *,
    username: str,
    password: str,
    secret: str,
):
    authentication_backend = AdminAuthenticationBackend(secret, username=username, password=password)
    admin = Admin(
        app,
        None,
        title="Engine panel",
        authentication_backend=authentication_backend,
        base_url="/admin",
    )
    admin.add_model_view(EngineView)
