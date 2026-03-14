from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock
from pytest import fixture

from app.domains.engine import EngineSpec
from app.services.engine import EngineService


@fixture()
def engine_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.specs = MagicMock()
    ctx.specs.get_engine_spec = AsyncMock(return_value=None)

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class EngineServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.svc = EngineService(uow)


class TestGetSpecByEngine(EngineServiceDeps):
    @pytest.mark.asyncio
    async def test_returns_engine_spec_when_found(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()
        spec = EngineSpec(
            engine_id=engine_id,
            config={"foo": "bar"},
            enabled=True,
            generation=7,
        )
        engine_ctx.specs.get_engine_spec.return_value = spec

        result = await self.svc.get_spec_by_engine(engine_id)

        assert result == spec
        uow.begin.assert_called_once_with(with_tx=False)
        engine_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)

    @pytest.mark.asyncio
    async def test_returns_none_when_spec_is_not_found(self, engine_ctx: MagicMock, uow: MagicMock):
        engine_id = uuid4()

        result = await self.svc.get_spec_by_engine(engine_id)

        assert result is None
        uow.begin.assert_called_once_with(with_tx=False)
        engine_ctx.specs.get_engine_spec.assert_awaited_once_with(engine_id)
