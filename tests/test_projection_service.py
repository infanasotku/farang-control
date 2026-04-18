from datetime import datetime, timezone
from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, call
from pytest import fixture

from app.domains.engine import Engine, EngineSpec
from app.domains.state import EngineRuntimeState, InstancePhase, SyncStatus
from app.services.projections.engine import EngineProjectionService


@fixture()
def projection_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.engines = MagicMock()
    ctx.specs = MagicMock()
    ctx.states = MagicMock()
    ctx.projections = MagicMock()

    ctx.engines.get_engine_by_id = AsyncMock(return_value=None)
    ctx.specs.get_engine_spec = AsyncMock(return_value=None)
    ctx.states.get_engine_state = AsyncMock(return_value=None)
    ctx.projections.upsert = AsyncMock()
    ctx.projections.delete = AsyncMock()

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class ProjectionServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.svc = EngineProjectionService(uow)


class TestSyncEngine(ProjectionServiceDeps):
    @pytest.mark.asyncio
    async def test_upserts_projection_from_engine_spec_and_state(self, projection_ctx: MagicMock, uow: MagicMock):
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

        assert uow.begin.call_args_list == [call(write=False), call(write=True)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        projection_ctx.states.get_engine_state.assert_awaited_once_with(engine_id)
        projection_ctx.projections.delete.assert_not_awaited()
        projection_ctx.projections.upsert.assert_awaited_once()

        upsert = projection_ctx.projections.upsert.await_args.args[0]
        assert upsert.engine_id == engine_id
        assert upsert.name == "test-engine"
        assert upsert.config == {"mode": "proxy"}
        assert upsert.enabled is True
        assert upsert.phase == InstancePhase.RUNNING
        assert upsert.last_seen_at == now
        assert upsert.sync == SyncStatus.IN_SYNC

    @pytest.mark.asyncio
    async def test_uses_defaults_when_spec_and_state_are_missing(self, projection_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        projection_ctx.engines.get_engine_by_id.return_value = Engine(id=engine_id, name="test-engine")

        await self.svc.sync_engine(engine_id)

        assert uow.begin.call_args_list == [call(write=False), call(write=True)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        projection_ctx.states.get_engine_state.assert_awaited_once_with(engine_id)
        projection_ctx.projections.delete.assert_not_awaited()
        projection_ctx.projections.upsert.assert_awaited_once()

        upsert = projection_ctx.projections.upsert.await_args.args[0]
        assert upsert.engine_id == engine_id
        assert upsert.name == "test-engine"
        assert upsert.config == {}
        assert upsert.enabled is False
        assert upsert.phase is None
        assert upsert.last_seen_at is None
        assert upsert.sync is None

    @pytest.mark.asyncio
    async def test_deletes_projection_when_engine_is_missing(self, projection_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()

        await self.svc.sync_engine(engine_id)

        assert uow.begin.call_args_list == [call(write=False), call(write=True)]
        projection_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        projection_ctx.specs.get_engine_spec.assert_not_awaited()
        projection_ctx.states.get_engine_state.assert_not_awaited()
        projection_ctx.projections.upsert.assert_not_awaited()
        projection_ctx.projections.delete.assert_awaited_once_with(engine_id)
