from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, patch
from pytest import fixture

from app.domains.engine import EngineSpec
from app.domains.exceptions.engine import EngineSpecNotFoundError
from app.dto.spec import UpdateSpecCmd
from app.services.spec import SpecService


@fixture()
def spec_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.specs = MagicMock()
    ctx.specs.get_engine_spec = AsyncMock(return_value=None)
    ctx.specs.get_engine_spec_for_update = AsyncMock(return_value=None)

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class SpecServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.svc = SpecService(uow)


class TestGetSpecByEngine(SpecServiceDeps):
    @pytest.mark.asyncio
    async def test_returns_engine_spec_when_found(self, spec_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"foo": "bar"},
            enabled=True,
            generation=7,
        )
        spec_ctx.specs.get_engine_spec.return_value = spec

        result = await self.svc.get_spec_by_engine(engine_id)

        assert result == spec
        uow.begin.assert_called_once_with(write=False)
        spec_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)

    @pytest.mark.asyncio
    async def test_returns_none_when_spec_is_not_found(self, spec_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()

        result = await self.svc.get_spec_by_engine(engine_id)

        assert result is None
        uow.begin.assert_called_once_with(write=False)
        spec_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)


class TestUpdateSpec(SpecServiceDeps):
    @pytest.mark.asyncio
    async def test_updates_spec_and_persists_when_changed(self, spec_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"foo": "bar"},
            enabled=True,
            generation=7,
        )
        spec_ctx.specs.get_engine_spec_for_update.return_value = spec
        cmd = UpdateSpecCmd(
            engine_id=engine_id,
            config={"foo": "baz"},
            enabled=False,
        )

        with patch("app.services.spec.upsert_engine_spec", new=AsyncMock()) as upsert_spec_mock:
            result = await self.svc.update_spec(cmd)

        assert result is None
        assert spec.config == {"foo": "baz"}
        assert spec.enabled is False
        assert spec.generation == 8
        uow.begin.assert_called_once_with(write=True)
        spec_ctx.specs.get_engine_spec_for_update.assert_awaited_once_with(engine_id)
        upsert_spec_mock.assert_awaited_once_with(spec, ctx=spec_ctx)

    @pytest.mark.asyncio
    async def test_persists_spec_without_generation_bump_when_nothing_changed(
        self,
        spec_ctx: MagicMock,
        uow: MagicMock,
    ):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"foo": "bar"},
            enabled=True,
            generation=7,
        )
        spec_ctx.specs.get_engine_spec_for_update.return_value = spec
        cmd = UpdateSpecCmd(
            engine_id=engine_id,
            config={"foo": "bar"},
            enabled=True,
        )

        with patch("app.services.spec.upsert_engine_spec", new=AsyncMock()) as upsert_spec_mock:
            result = await self.svc.update_spec(cmd)

        assert result is None
        assert spec.config == {"foo": "bar"}
        assert spec.enabled is True
        assert spec.generation == 7
        uow.begin.assert_called_once_with(write=True)
        spec_ctx.specs.get_engine_spec_for_update.assert_awaited_once_with(engine_id)
        upsert_spec_mock.assert_awaited_once_with(spec, ctx=spec_ctx)

    @pytest.mark.asyncio
    async def test_raises_when_spec_is_not_found(self, spec_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        cmd = UpdateSpecCmd(
            engine_id=engine_id,
            config={"foo": "baz"},
            enabled=False,
        )

        with patch("app.services.spec.upsert_engine_spec", new=AsyncMock()) as upsert_spec_mock:
            with pytest.raises(EngineSpecNotFoundError):
                await self.svc.update_spec(cmd)

        uow.begin.assert_called_once_with(write=True)
        spec_ctx.specs.get_engine_spec_for_update.assert_awaited_once_with(engine_id)
        upsert_spec_mock.assert_not_awaited()
