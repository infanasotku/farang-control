from mock import AsyncMock, MagicMock
from pytest import fixture

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
    pass
