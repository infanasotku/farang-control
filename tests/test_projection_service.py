from datetime import datetime, timezone
from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, call, patch
from pytest import fixture

from app.domains.engine import Engine, EngineSpec
from app.domains.state import EngineRuntimeState, InstancePhase, LivenessStatus, SyncStatus
from app.dto.projections import Projection, StartSyncAllProjectionsCmd
from app.services.projections.engine import EngineProjectionService


@fixture()
def repo() -> MagicMock:
    repo = MagicMock()
    repo.get = AsyncMock(return_value=[])
    repo.upsert = AsyncMock()
    repo.delete = AsyncMock()
    repo.try_lock_syncing = AsyncMock(return_value=None)
    return repo


@fixture()
def projection_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.engines = MagicMock()
    ctx.specs = MagicMock()
    ctx.states = MagicMock()

    ctx.engines.get_engine_by_id = AsyncMock(return_value=None)
    ctx.specs.get_engine_spec = AsyncMock(return_value=None)
    ctx.states.get_engine_state = AsyncMock(return_value=None)

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class ProjectionServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock, repo: MagicMock):
        self.svc = EngineProjectionService(uow, repo=repo)


class TestGet(ProjectionServiceDeps):
    @pytest.mark.asyncio
    async def test_returns_derived_projections_with_liveness(self, repo: MagicMock):
        engine_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        last_seen_at = datetime(2026, 3, 14, tzinfo=timezone.utc)
        repo.get.return_value = [
            Projection(
                engine_id=engine_id,
                name="test-engine",
                config={"mode": "proxy"},
                enabled=True,
                phase=InstancePhase.RUNNING,
                last_seen_at=last_seen_at,
                sync=SyncStatus.IN_SYNC,
            )
        ]

        with patch("app.services.projections.engine.now_utc", return_value=now):
            result = await self.svc.get(offset=10, limit=20)

        repo.get.assert_awaited_once_with(offset=10, limit=20)
        assert len(result) == 1

        row = result[0]
        assert row.engine_id == engine_id
        assert row.name == "test-engine"
        assert row.config == {"mode": "proxy"}
        assert row.enabled is True
        assert row.phase == InstancePhase.RUNNING
        assert row.last_seen_at == last_seen_at
        assert row.sync == SyncStatus.IN_SYNC
        assert row.liveness == LivenessStatus.DEAD

    @pytest.mark.asyncio
    async def test_returns_derived_projections_without_liveness_when_last_seen_is_missing(self, repo: MagicMock):
        engine_id = uuid4()
        repo.get.return_value = [
            Projection(
                engine_id=engine_id,
                name="test-engine",
                config={},
                enabled=False,
            )
        ]

        result = await self.svc.get()

        repo.get.assert_awaited_once_with(offset=0, limit=100)
        assert len(result) == 1
        assert result[0].engine_id == engine_id
        assert result[0].liveness is None


class TestSyncEngine(ProjectionServiceDeps):
    @pytest.mark.asyncio
    async def test_upserts_projection_from_engine_spec_and_state(
        self, projection_ctx: MagicMock, uow: MagicMock, repo: MagicMock
    ):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)

        projection_ctx.engines.get_engine_by_id.return_value = Engine(id=engine_id, name="test-engine")
        projection_ctx.specs.get_engine_spec.return_value = EngineSpec(
            engine_id=engine_id,
            config={"mode": "proxy"},
            enabled=True,
            generation=4,
        )
        projection_ctx.states.get_engine_state.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.RUNNING,
            observed_generation=4,
            last_seen_at=now,
            last_seq_no=7,
            current_instance_id=instance_id,
            current_epoch=2,
        )

        await self.svc.sync_engine(engine_id)

        assert uow.begin.call_args_list == [call(write=False)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        projection_ctx.states.get_engine_state.assert_awaited_once_with(engine_id)
        repo.delete.assert_not_awaited()
        repo.upsert.assert_awaited_once()

        upsert = repo.upsert.await_args.args[0]
        assert upsert.engine_id == engine_id
        assert upsert.name == "test-engine"
        assert upsert.config == {"mode": "proxy"}
        assert upsert.enabled is True
        assert upsert.phase == InstancePhase.RUNNING
        assert upsert.last_seen_at == now
        assert upsert.sync == SyncStatus.IN_SYNC

    @pytest.mark.asyncio
    async def test_uses_defaults_when_spec_and_state_are_missing(
        self, projection_ctx: MagicMock, uow: MagicMock, repo: MagicMock
    ):
        engine_id = uuid4()
        projection_ctx.engines.get_engine_by_id.return_value = Engine(id=engine_id, name="test-engine")

        await self.svc.sync_engine(engine_id)

        assert uow.begin.call_args_list == [call(write=False)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        projection_ctx.states.get_engine_state.assert_awaited_once_with(engine_id)
        repo.delete.assert_not_awaited()
        repo.upsert.assert_awaited_once()

        upsert = repo.upsert.await_args.args[0]
        assert upsert.engine_id == engine_id
        assert upsert.name == "test-engine"
        assert upsert.config == {}
        assert upsert.enabled is False
        assert upsert.phase is None
        assert upsert.last_seen_at is None
        assert upsert.sync is None

    @pytest.mark.asyncio
    async def test_deletes_projection_when_engine_is_missing(
        self, projection_ctx: MagicMock, uow: MagicMock, repo: MagicMock
    ):
        engine_id = uuid4()

        await self.svc.sync_engine(engine_id)

        assert uow.begin.call_args_list == [call(write=False)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_not_awaited()
        projection_ctx.states.get_engine_state.assert_not_awaited()
        repo.upsert.assert_not_awaited()
        repo.delete.assert_awaited_once_with(engine_id)


class TestStartSyncAllProjections(ProjectionServiceDeps):
    @pytest.mark.asyncio
    async def test_starts_task_when_lock_is_acquired(self, repo: MagicMock):
        repo.try_lock_syncing.return_value = "lock-token"
        cmd = StartSyncAllProjectionsCmd(correlation_id="correlation-id")

        with patch("app.controllers.tasks.projections.sync_all_projections_task") as task:
            await self.svc.start_sync_all_projections(cmd)

        repo.try_lock_syncing.assert_awaited_once_with()
        task.apply_async.assert_called_once_with(
            kwargs={"lock_token": "lock-token"},
            task_id="correlation-id",
        )

    @pytest.mark.asyncio
    async def test_does_not_start_task_when_lock_is_not_acquired(self, repo: MagicMock):
        repo.try_lock_syncing.return_value = None
        cmd = StartSyncAllProjectionsCmd(correlation_id="correlation-id")

        with patch("app.controllers.tasks.projections.sync_all_projections_task") as task:
            await self.svc.start_sync_all_projections(cmd)

        repo.try_lock_syncing.assert_awaited_once_with()
        task.apply_async.assert_not_called()
