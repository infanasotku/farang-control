from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, patch
from pytest import fixture

from app.domains.engine import Engine, EngineSpec
from app.domains.exceptions.engine import EngineNotFoundError
from app.services.engine import EngineService


@fixture()
def engine_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.engines = MagicMock()
    ctx.specs = MagicMock()
    ctx.engines.get_engine_by_id = AsyncMock(return_value=None)
    ctx.engines.add = AsyncMock()
    ctx.engines.update = AsyncMock()
    ctx.engines.delete = AsyncMock()
    ctx.specs.get_engine_spec = AsyncMock(return_value=None)

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class EngineServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.svc = EngineService(uow)


class TestUpdateEngine(EngineServiceDeps):
    @pytest.mark.asyncio
    async def test_updates_engine_when_found(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        engine = Engine(id=engine_id, name="old-name")
        engine_ctx.engines.get_engine_by_id.return_value = engine

        result = await self.svc.update_engine(engine_id, "new-name")

        assert result is engine
        assert engine.name == "new-name"
        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        engine_ctx.engines.update.assert_awaited_once_with(engine)

    @pytest.mark.asyncio
    async def test_raises_when_engine_is_not_found(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()

        with pytest.raises(EngineNotFoundError):
            await self.svc.update_engine(engine_id, "new-name")

        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        engine_ctx.engines.update.assert_not_awaited()


class TestCreateEngine(EngineServiceDeps):
    @pytest.mark.asyncio
    async def test_creates_engine_and_initial_spec(self, engine_ctx: MagicMock, uow: MagicMock):
        with patch("app.services.engine.upsert_engine_spec", new=AsyncMock()) as upsert_spec_mock:
            result = await self.svc.create_engine("test-engine")

        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.add.assert_awaited_once_with(result)
        assert result.name == "test-engine"

        await_args = upsert_spec_mock.await_args
        assert await_args is not None
        created_spec = await_args.args[0]
        assert created_spec == EngineSpec.initial(result.id)
        upsert_spec_mock.assert_awaited_once_with(created_spec, ctx=engine_ctx)


class TestRemoveEngine(EngineServiceDeps):
    @pytest.mark.asyncio
    async def test_raises_when_engine_is_not_found(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()

        with pytest.raises(EngineNotFoundError):
            await self.svc.remove_engine(engine_id)

        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        engine_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        engine_ctx.engines.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_removes_engine_and_spec_when_spec_exists(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        engine = Engine(id=engine_id, name="test-engine")
        spec = EngineSpec.initial(engine_id)
        engine_ctx.engines.get_engine_by_id.return_value = engine
        engine_ctx.specs.get_engine_spec.return_value = spec

        with patch("app.services.engine.remove_engine_spec", new=AsyncMock()) as remove_spec_mock:
            result = await self.svc.remove_engine(engine_id)

        assert result is None
        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.get_engine_by_id.assert_awaited_once_with(engine_id)
        engine_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
        engine_ctx.engines.delete.assert_awaited_once_with(engine_id)
        remove_spec_mock.assert_awaited_once_with(spec, ctx=engine_ctx)

    @pytest.mark.asyncio
    async def test_removes_engine_without_spec_side_effect_when_spec_is_missing(
        self,
        engine_ctx: MagicMock,
        uow: MagicMock,
    ):
        engine_id = uuid4()
        engine = Engine(id=engine_id, name="test-engine")
        engine_ctx.engines.get_engine_by_id.return_value = engine
        engine_ctx.specs.get_engine_spec.return_value = None

        with patch("app.services.engine.remove_engine_spec", new=AsyncMock()) as remove_spec_mock:
            result = await self.svc.remove_engine(engine_id)

        assert result is None
        uow.begin.assert_called_once_with(write=True)
        engine_ctx.engines.delete.assert_awaited_once_with(engine_id)
        remove_spec_mock.assert_not_awaited()
