from datetime import datetime, timezone
from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, patch
from pytest import fixture

from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import CurrentInstanceAliveError, InstanceDeprecatedError, InstanceNotRegisteredError
from app.domains.state import EngineInstance, EngineRuntimeState, InstancePhase
from app.dto.state import ApplyHeartbeatCmd
from app.services.state import StateService


@fixture()
def state_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.engines = MagicMock()
    ctx.states = MagicMock()
    ctx.instances = MagicMock()
    ctx.engines.get_engine_for_update = AsyncMock(return_value=MagicMock())
    ctx.engines.get_engine_by_id = AsyncMock(return_value=MagicMock())
    ctx.states.get_engine_state_for_update = AsyncMock(return_value=None)
    ctx.states.upsert_engine_state = AsyncMock()
    ctx.instances.get_instance_by_id = AsyncMock(return_value=None)
    ctx.instances.create = AsyncMock()

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class StateServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.projection = MagicMock()
        self.projection.sync_engine = AsyncMock()
        self.svc = StateService(uow, projection=self.projection)


class TestRegisterInstance(StateServiceDeps):
    @pytest.mark.asyncio
    async def test_non_exist_engine_causes_engine_not_found_error(self, state_ctx: MagicMock):
        state_ctx.engines.get_engine_for_update = AsyncMock(return_value=None)

        with pytest.raises(EngineNotFoundError):
            await self.svc.register_instance(
                instance_id=uuid4(),
                engine_id=uuid4(),
            )

        state_ctx.instances.create.assert_not_awaited()
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_current_instance_retry_returns_existing_epoch_without_writes(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=0,
            current_instance_id=instance_id,
            current_epoch=3,
        )
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=3,
            created_at=now,
        )

        epoch = await self.svc.register_instance(instance_id=instance_id, engine_id=engine_id)

        assert epoch == 3
        state_ctx.instances.create.assert_not_awaited()
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_retired_instance_causes_instance_deprecated_error(self, state_ctx: MagicMock):
        engine_id = uuid4()
        current_instance_id = uuid4()
        requested_instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=0,
            current_instance_id=current_instance_id,
            current_epoch=4,
        )
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=requested_instance_id,
            engine_id=engine_id,
            epoch=2,
            created_at=now,
        )

        with pytest.raises(InstanceDeprecatedError):
            await self.svc.register_instance(
                instance_id=requested_instance_id,
                engine_id=engine_id,
            )

        state_ctx.instances.create.assert_not_awaited()
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_alive_current_instance_causes_current_instance_alive_error(self, state_ctx: MagicMock):
        engine_id = uuid4()
        current_instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=0,
            current_instance_id=current_instance_id,
            current_epoch=2,
        )

        with patch("app.services.state.now_utc", return_value=now):
            with pytest.raises(CurrentInstanceAliveError):
                await self.svc.register_instance(
                    instance_id=uuid4(),
                    engine_id=engine_id,
                )

        state_ctx.instances.create.assert_not_awaited()
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_first_registration_creates_instance_and_runtime_state(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)

        with patch("app.services.state.now_utc", return_value=now):
            epoch = await self.svc.register_instance(
                instance_id=instance_id,
                engine_id=engine_id,
            )

        assert epoch == 1
        state_ctx.instances.create.assert_awaited_once()
        state_ctx.states.upsert_engine_state.assert_awaited_once()

        created_instance = state_ctx.instances.create.await_args.args[0]
        assert created_instance.instance_id == instance_id
        assert created_instance.engine_id == engine_id
        assert created_instance.epoch == 1
        assert created_instance.created_at == now

        created_state = state_ctx.states.upsert_engine_state.await_args.args[0]
        assert created_state.engine_id == engine_id
        assert created_state.current_instance_id == instance_id
        assert created_state.current_epoch == 1
        assert created_state.reported_phase == InstancePhase.STARTING
        assert created_state.observed_generation == 0
        assert created_state.last_seq_no == 0
        assert created_state.last_seen_at == now
        self.projection.sync_engine.assert_awaited_once_with(engine_id)

    @pytest.mark.asyncio
    async def test_registration_after_dead_instance_creates_new_epoch(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        dead_instance_id = uuid4()
        now = datetime(2026, 3, 15, 0, 10, tzinfo=timezone.utc)
        dead_seen_at = datetime(2026, 3, 15, 0, 0, tzinfo=timezone.utc)
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=dead_seen_at,
            last_seq_no=0,
            current_instance_id=dead_instance_id,
            current_epoch=7,
        )

        with patch("app.services.state.now_utc", return_value=now):
            epoch = await self.svc.register_instance(
                instance_id=instance_id,
                engine_id=engine_id,
            )

        assert epoch == 8
        state_ctx.instances.create.assert_awaited_once()
        state_ctx.states.upsert_engine_state.assert_awaited_once()

        created_instance = state_ctx.instances.create.await_args.args[0]
        assert created_instance.instance_id == instance_id
        assert created_instance.epoch == 8

        created_state = state_ctx.states.upsert_engine_state.await_args.args[0]
        assert created_state.current_instance_id == instance_id
        assert created_state.current_epoch == 8
        self.projection.sync_engine.assert_awaited_once_with(engine_id)

    @pytest.mark.asyncio
    async def test_registration_succeeds_when_projection_sync_fails(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        self.projection.sync_engine.side_effect = RuntimeError("projection failed")

        with (
            patch("app.services.state.now_utc", return_value=now),
            patch("app.services.state.logger.exception") as logger_exception,
        ):
            epoch = await self.svc.register_instance(
                instance_id=instance_id,
                engine_id=engine_id,
            )

        assert epoch == 1
        state_ctx.instances.create.assert_awaited_once()
        state_ctx.states.upsert_engine_state.assert_awaited_once()
        self.projection.sync_engine.assert_awaited_once_with(engine_id)
        logger_exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_existing_instance_without_runtime_state_causes_runtime_error(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=1,
            created_at=now,
        )

        with pytest.raises(RuntimeError, match="Inconsistent state"):
            await self.svc.register_instance(
                instance_id=instance_id,
                engine_id=engine_id,
            )

        state_ctx.instances.create.assert_not_awaited()
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()


class TestApplyHeartbeat(StateServiceDeps):
    @pytest.mark.asyncio
    async def test_non_exist_engine_causes_engine_not_found_error(self, state_ctx: MagicMock):
        cmd = ApplyHeartbeatCmd(
            engine_id=uuid4(),
            instance_id=uuid4(),
            epoch=1,
            seq_no=1,
            phase=InstancePhase.STARTING,
            generation=0,
        )
        state_ctx.engines.get_engine_by_id.return_value = None

        with pytest.raises(EngineNotFoundError):
            await self.svc.apply_heartbeat(cmd)

        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unregistered_instance_causes_instance_not_registered_error(self, state_ctx: MagicMock):
        cmd = ApplyHeartbeatCmd(
            engine_id=uuid4(),
            instance_id=uuid4(),
            epoch=1,
            seq_no=1,
            phase=InstancePhase.STARTING,
            generation=0,
        )

        with pytest.raises(InstanceNotRegisteredError):
            await self.svc.apply_heartbeat(cmd)

        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_old_instance_is_ignored_without_writes(self, state_ctx: MagicMock):
        engine_id = uuid4()
        current_instance_id = uuid4()
        requested_instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        cmd = ApplyHeartbeatCmd(
            engine_id=engine_id,
            instance_id=requested_instance_id,
            epoch=4,
            seq_no=2,
            phase=InstancePhase.STARTING,
            generation=0,
        )
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=1,
            current_instance_id=current_instance_id,
            current_epoch=4,
        )
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=requested_instance_id,
            engine_id=engine_id,
            epoch=4,
            created_at=now,
        )

        result = await self.svc.apply_heartbeat(cmd)

        assert result is None
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_old_epoch_is_ignored_without_writes(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        cmd = ApplyHeartbeatCmd(
            engine_id=engine_id,
            instance_id=instance_id,
            epoch=3,
            seq_no=2,
            phase=InstancePhase.STARTING,
            generation=0,
        )
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=1,
            current_instance_id=instance_id,
            current_epoch=4,
        )
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=3,
            created_at=now,
        )

        result = await self.svc.apply_heartbeat(cmd)

        assert result is None
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_duplicate_or_old_seq_no_is_ignored_without_writes(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        cmd = ApplyHeartbeatCmd(
            engine_id=engine_id,
            instance_id=instance_id,
            epoch=3,
            seq_no=5,
            phase=InstancePhase.STARTING,
            generation=1,
        )
        state_ctx.states.get_engine_state_for_update.return_value = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=5,
            current_instance_id=instance_id,
            current_epoch=3,
        )
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=3,
            created_at=now,
        )

        with patch("app.services.state.now_utc", return_value=now):
            result = await self.svc.apply_heartbeat(cmd)

        assert result is None
        state_ctx.states.upsert_engine_state.assert_not_awaited()
        self.projection.sync_engine.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_new_heartbeat_updates_runtime_state(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        previous_seen_at = datetime(2026, 3, 15, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 3, 15, 0, 1, tzinfo=timezone.utc)
        cmd = ApplyHeartbeatCmd(
            engine_id=engine_id,
            instance_id=instance_id,
            epoch=2,
            seq_no=7,
            phase=InstancePhase.STARTING,
            generation=5,
        )
        state = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=1,
            last_seen_at=previous_seen_at,
            last_seq_no=6,
            current_instance_id=instance_id,
            current_epoch=2,
        )
        state_ctx.states.get_engine_state_for_update.return_value = state
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=2,
            created_at=previous_seen_at,
        )

        with patch("app.services.state.now_utc", return_value=now):
            result = await self.svc.apply_heartbeat(cmd)

        assert result is None
        state_ctx.states.upsert_engine_state.assert_awaited_once_with(state)
        assert state.reported_phase == InstancePhase.STARTING
        assert state.observed_generation == 5
        assert state.last_seq_no == 7
        assert state.last_seen_at == now
        self.projection.sync_engine.assert_awaited_once_with(engine_id)

    @pytest.mark.asyncio
    async def test_heartbeat_succeeds_when_projection_sync_fails(self, state_ctx: MagicMock):
        engine_id = uuid4()
        instance_id = uuid4()
        previous_seen_at = datetime(2026, 3, 15, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 3, 15, 0, 1, tzinfo=timezone.utc)
        self.projection.sync_engine.side_effect = RuntimeError("projection failed")
        cmd = ApplyHeartbeatCmd(
            engine_id=engine_id,
            instance_id=instance_id,
            epoch=2,
            seq_no=7,
            phase=InstancePhase.STARTING,
            generation=5,
        )
        state = EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.STARTING,
            observed_generation=1,
            last_seen_at=previous_seen_at,
            last_seq_no=6,
            current_instance_id=instance_id,
            current_epoch=2,
        )
        state_ctx.states.get_engine_state_for_update.return_value = state
        state_ctx.instances.get_instance_by_id.return_value = EngineInstance(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=2,
            created_at=previous_seen_at,
        )

        with (
            patch("app.services.state.now_utc", return_value=now),
            patch("app.services.state.logger.exception") as logger_exception,
        ):
            result = await self.svc.apply_heartbeat(cmd)

        assert result is None
        state_ctx.states.upsert_engine_state.assert_awaited_once_with(state)
        self.projection.sync_engine.assert_awaited_once_with(engine_id)
        logger_exception.assert_called_once()
