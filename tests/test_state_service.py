from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock
from pytest import fixture

from app.services.exceptions.engine import EngineNotFoundError
from app.services.state import StateService


@fixture()
def state_ctx(uow: MagicMock):
    ctx = MagicMock()
    ctx.engines = MagicMock()
    ctx.states = MagicMock()
    ctx.instances = MagicMock()

    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


class StateServiceDeps:
    @fixture(autouse=True)
    def _setup(self, uow: MagicMock):
        self.svc = StateService(uow)


class TestRegisterInstance(StateServiceDeps):
    @pytest.mark.asyncio
    async def test_non_exist_engine_causes_engine_not_found_error(self, state_ctx: MagicMock):
        state_ctx.engines.get_engine_for_update = AsyncMock(return_value=None)

        with pytest.raises(EngineNotFoundError):
            await self.svc.register_instance(
                instance_id=uuid4(),
                engine_id=uuid4(),
            )
