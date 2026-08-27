from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from dependency_injector import providers
from fastapi.testclient import TestClient
from mock import AsyncMock, MagicMock
from pytest import fixture

from app.container import Container
from app.controllers.api.utils.auth import authenticate, authenticate_operator
from app.domains.engine import EngineSpec
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import (
    CurrentInstanceAliveError,
    EngineHasNoRuntimeStateError,
    InstanceDeprecatedError,
    InstanceNotRegisteredError,
)
from app.domains.state import InstancePhase
from app.dto.state import ReplacementPermit
from app.entrypoints.api import create_app


@fixture()
def engine_service() -> MagicMock:
    svc = MagicMock()
    return svc


@fixture()
def state_service() -> MagicMock:
    svc = MagicMock()
    svc.register_instance = AsyncMock()
    svc.apply_heartbeat = AsyncMock()
    svc.issue_replacement_permit = AsyncMock()
    svc.revoke_replacement_permit = AsyncMock()
    return svc


@fixture()
def spec_service() -> MagicMock:
    svc = MagicMock()
    svc.get_spec_by_engine = AsyncMock()
    return svc


@asynccontextmanager
async def redis_context():
    yield MagicMock()


@fixture()
def client(engine_service: MagicMock, state_service: MagicMock, spec_service: MagicMock):
    Container.engine_service.override(providers.Object(engine_service))
    Container.state_service.override(providers.Object(state_service))
    Container.spec_service.override(providers.Object(spec_service))
    Container.redis.override(providers.Resource(redis_context))

    app = create_app()
    app.dependency_overrides[authenticate] = lambda: None
    app.dependency_overrides[authenticate_operator] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Container.engine_service.reset_override()
    Container.state_service.reset_override()
    Container.spec_service.reset_override()
    Container.redis.reset_override()


class TestAdminAssets:
    def test_serves_json_editor(self, client: TestClient):
        response = client.get("/admin-assets/json-editor.js")

        assert response.status_code == 200
        assert "CodeMirror.fromTextArea" in response.text
        assert response.headers["content-type"].startswith("text/javascript")


class TestGetEngineSpecRoute:
    def test_returns_spec_when_found(self, client: TestClient, spec_service: MagicMock):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"mode": "proxy"},
            enabled=True,
            generation=12,
        )
        spec_service.get_spec_by_engine.return_value = spec

        response = client.get(f"/api/v1/engines/{engine_id}/spec")

        assert response.status_code == 200
        assert response.json() == {
            "engine_id": str(engine_id),
            "config": {"mode": "proxy"},
            "enabled": True,
            "generation": 12,
            "config_hash": spec.config_hash,
        }
        spec_service.get_spec_by_engine.assert_awaited_once_with(engine_id)

    def test_returns_404_when_spec_is_not_found(self, client: TestClient, spec_service: MagicMock):
        engine_id = uuid4()
        spec_service.get_spec_by_engine.return_value = None

        response = client.get(f"/api/v1/engines/{engine_id}/spec")

        assert response.status_code == 404
        assert response.json() == {"detail": "Engine spec is not found"}
        spec_service.get_spec_by_engine.assert_awaited_once_with(engine_id)

    def test_returns_422_for_invalid_engine_id(self, client: TestClient, spec_service: MagicMock):
        response = client.get("/api/v1/engines/not-a-uuid/spec")

        assert response.status_code == 422
        spec_service.get_spec_by_engine.assert_not_called()


class TestRegisterEngineInstanceRoute:
    def test_returns_epoch_when_registration_succeeds(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.return_value = 7

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 200
        assert response.json() == {"epoch": 7}
        state_service.register_instance.assert_awaited_once_with(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit=None,
        )

    def test_forwards_replacement_permit_header(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.return_value = 8

        response = client.post(
            f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}",
            headers={"X-Replacement-Permit": "one-time-permit"},
        )

        assert response.status_code == 200
        state_service.register_instance.assert_awaited_once_with(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit="one-time-permit",
        )

    def test_returns_404_when_engine_is_not_found(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.side_effect = EngineNotFoundError(engine_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Engine with id {engine_id} is not found"}
        state_service.register_instance.assert_awaited_once_with(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit=None,
        )

    def test_returns_409_when_current_instance_is_alive(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        current_instance_id = uuid4()
        state_service.register_instance.side_effect = CurrentInstanceAliveError(current_instance_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 409
        assert response.json() == {"detail": f"Another instance {current_instance_id} is still alive"}
        state_service.register_instance.assert_awaited_once_with(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit=None,
        )

    def test_returns_410_when_instance_is_deprecated(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.register_instance.side_effect = InstanceDeprecatedError(instance_id)

        response = client.post(f"/api/v1/engines/{engine_id}/register-instance?instance_id={instance_id}")

        assert response.status_code == 410
        assert response.json() == {"detail": f"Instance {instance_id} is deprecated"}
        state_service.register_instance.assert_awaited_once_with(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit=None,
        )

    def test_returns_422_for_invalid_path_or_query_uuid(self, client: TestClient, state_service: MagicMock):
        response = client.post("/api/v1/engines/not-a-uuid/register-instance?instance_id=bad-uuid")

        assert response.status_code == 422
        state_service.register_instance.assert_not_called()


class TestReplacementPermitRoutes:
    def test_issues_replacement_permit(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        current_instance_id = uuid4()
        expires_at = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)
        state_service.issue_replacement_permit.return_value = ReplacementPermit(
            engine_id=engine_id,
            current_instance_id=current_instance_id,
            permit="one-time-permit",
            expires_at=expires_at,
        )

        response = client.post(f"/api/v1/management/engines/{engine_id}/replacement-permit")

        assert response.status_code == 201
        assert response.json() == {
            "engine_id": str(engine_id),
            "current_instance_id": str(current_instance_id),
            "permit": "one-time-permit",
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        }
        state_service.issue_replacement_permit.assert_awaited_once_with(engine_id=engine_id)

    def test_issue_returns_404_when_engine_is_not_found(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        state_service.issue_replacement_permit.side_effect = EngineNotFoundError(engine_id)

        response = client.post(f"/api/v1/management/engines/{engine_id}/replacement-permit")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Engine with id {engine_id} is not found"}

    def test_issue_returns_409_without_runtime_owner(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        state_service.issue_replacement_permit.side_effect = EngineHasNoRuntimeStateError(engine_id)

        response = client.post(f"/api/v1/management/engines/{engine_id}/replacement-permit")

        assert response.status_code == 409
        assert response.json() == {"detail": f"Engine {engine_id} has no runtime owner"}

    def test_revokes_replacement_permit(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()

        response = client.delete(f"/api/v1/management/engines/{engine_id}/replacement-permit")

        assert response.status_code == 204
        assert response.content == b""
        state_service.revoke_replacement_permit.assert_awaited_once_with(engine_id=engine_id)

    def test_revoke_returns_404_when_engine_is_not_found(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        state_service.revoke_replacement_permit.side_effect = EngineNotFoundError(engine_id)

        response = client.delete(f"/api/v1/management/engines/{engine_id}/replacement-permit")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Engine with id {engine_id} is not found"}


class TestHeartbeatRoute:
    def test_returns_200_when_heartbeat_succeeds(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()

        response = client.post(
            f"/api/v1/engines/{engine_id}/heartbeat",
            json={
                "instance_id": str(instance_id),
                "epoch": 2,
                "seq_no": 7,
                "phase": InstancePhase.STARTING.value,
                "generation": 5,
            },
        )

        assert response.status_code == 200
        assert response.json() is None
        state_service.apply_heartbeat.assert_awaited_once()
        cmd = state_service.apply_heartbeat.await_args.args[0]
        assert cmd.engine_id == engine_id
        assert cmd.instance_id == instance_id
        assert cmd.epoch == 2
        assert cmd.seq_no == 7
        assert cmd.phase == InstancePhase.STARTING
        assert cmd.generation == 5

    def test_returns_404_when_engine_is_not_found(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.apply_heartbeat.side_effect = EngineNotFoundError(engine_id)

        response = client.post(
            f"/api/v1/engines/{engine_id}/heartbeat",
            json={
                "instance_id": str(instance_id),
                "epoch": 2,
                "seq_no": 7,
                "phase": InstancePhase.STARTING.value,
                "generation": 5,
            },
        )

        assert response.status_code == 404
        assert response.json() == {"detail": f"Engine with id {engine_id} is not found"}
        state_service.apply_heartbeat.assert_awaited_once()

    def test_returns_200_when_old_instance_heartbeat_is_ignored(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()

        response = client.post(
            f"/api/v1/engines/{engine_id}/heartbeat",
            json={
                "instance_id": str(instance_id),
                "epoch": 1,
                "seq_no": 7,
                "phase": InstancePhase.STARTING.value,
                "generation": 5,
            },
        )

        assert response.status_code == 200
        assert response.json() is None
        state_service.apply_heartbeat.assert_awaited_once()

    def test_returns_409_when_instance_is_not_registered(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        state_service.apply_heartbeat.side_effect = InstanceNotRegisteredError(instance_id)

        response = client.post(
            f"/api/v1/engines/{engine_id}/heartbeat",
            json={
                "instance_id": str(instance_id),
                "epoch": 2,
                "seq_no": 7,
                "phase": InstancePhase.STARTING.value,
                "generation": 5,
            },
        )

        assert response.status_code == 409
        assert response.json() == {"detail": f"Instance {instance_id} is not registered"}
        state_service.apply_heartbeat.assert_awaited_once()

    def test_returns_422_for_invalid_payload(self, client: TestClient, state_service: MagicMock):
        engine_id = uuid4()

        response = client.post(
            f"/api/v1/engines/{engine_id}/heartbeat",
            json={
                "instance_id": "bad-uuid",
                "epoch": "bad-int",
                "seq_no": 7,
                "phase": "bad-phase",
                "generation": 5,
            },
        )

        assert response.status_code == 422
        state_service.apply_heartbeat.assert_not_called()
