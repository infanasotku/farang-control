from uuid import uuid4

from dependency_injector import providers
from fastapi.testclient import TestClient
from mock import AsyncMock, MagicMock
from pytest import fixture

from app.container import Container
from app.controllers.api.utils.auth import authenticate
from app.domains.engine import EngineSpec
from app.domains.exceptions.state import CurrentInstanceAliveError, InstanceDeprecatedError
from app.entrypoints.api import create_app
from app.services.exceptions.engine import EngineNotFoundError


@fixture()
def engine_service() -> MagicMock:
    svc = MagicMock()
    svc.get_spec_by_engine = AsyncMock()
    return svc


@fixture()
def state_service() -> MagicMock:
    svc = MagicMock()
    svc.register_instance = AsyncMock()
    return svc


@fixture()
def client(engine_service: MagicMock, state_service: MagicMock):
    Container.spec_service.override(providers.Object(engine_service))
    Container.state_service.override(providers.Object(state_service))

    app = create_app()
    app.dependency_overrides[authenticate] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Container.spec_service.reset_override()
    Container.state_service.reset_override()


class TestGetEngineSpecRoute:
    def test_returns_spec_when_found(self, client: TestClient, engine_service: MagicMock):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"mode": "proxy"},
            enabled=True,
            generation=12,
        )
        engine_service.get_spec_by_engine.return_value = spec

        response = client.get(f"/api/v1/engines/{engine_id}/spec")

        assert response.status_code == 200
        assert response.json() == {
            "engine_id": str(engine_id),
            "config": {"mode": "proxy"},
            "enabled": True,
            "generation": 12,
            "config_hash": spec.config_hash,
        }
        engine_service.get_spec_by_engine.assert_awaited_once_with(engine_id)

    def test_returns_404_when_spec_is_not_found(self, client: TestClient, engine_service: MagicMock):
        engine_id = uuid4()
        engine_service.get_spec_by_engine.return_value = None

        response = client.get(f"/api/v1/engines/{engine_id}/spec")

        assert response.status_code == 404
        assert response.json() == {"detail": "Engine spec is not found"}
        engine_service.get_spec_by_engine.assert_awaited_once_with(engine_id)

    def test_returns_422_for_invalid_engine_id(self, client: TestClient, engine_service: MagicMock):
        response = client.get("/api/v1/engines/not-a-uuid/spec")

        assert response.status_code == 422
        engine_service.get_spec_by_engine.assert_not_called()


class TestRegisterEngineInstanceRoute:
    def test_returns_epoch_when_registration_succeeds(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.return_value = 7

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 200
        assert response.json() == {"epoch": 7}
        state_service.register_instance.assert_awaited_once_with(instance_id=instance_id, engine_id=engine_id)

    def test_returns_404_when_engine_is_not_found(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.side_effect = EngineNotFoundError(engine_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Engine with id {engine_id} is not found"}
        state_service.register_instance.assert_awaited_once_with(instance_id=instance_id, engine_id=engine_id)

    def test_returns_409_when_current_instance_is_alive(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        current_instance_id = uuid4()
        state_service.register_instance.side_effect = CurrentInstanceAliveError(current_instance_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 409
        assert response.json() == {"detail": f"Another instance {current_instance_id} is still alive"}
        state_service.register_instance.assert_awaited_once_with(instance_id=instance_id, engine_id=engine_id)

    def test_returns_410_when_instance_is_deprecated(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.side_effect = InstanceDeprecatedError(instance_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 410
        assert response.json() == {"detail": f"Instance {instance_id} is deprecated"}
        state_service.register_instance.assert_awaited_once_with(instance_id=instance_id, engine_id=engine_id)

    def test_returns_422_for_invalid_path_or_query_uuid(self, client: TestClient, state_service: MagicMock):
        response = client.post("/api/v1/engines/not-a-uuid/register-instance?instance_id=bad-uuid")

        assert response.status_code == 422
        state_service.register_instance.assert_not_called()
