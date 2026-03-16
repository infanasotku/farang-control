from uuid import uuid4

import pytest
from mock import AsyncMock, MagicMock, patch
from pytest import fixture

from app.domains.engine import EngineSpec
from app.services.shared.spec import remove_engine_spec, upsert_engine_spec


@fixture()
def spec_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.specs = MagicMock()
    ctx.specs.upsert = AsyncMock()
    ctx.specs.delete_by_engine = AsyncMock()
    return ctx


class TestUpsertEngineSpec:
    @pytest.mark.asyncio
    async def test_upserts_spec_and_saves_event(self, spec_ctx: MagicMock):
        spec = EngineSpec(
            engine_id=uuid4(),
            config={"mode": "proxy"},
            enabled=True,
            generation=3,
        )

        with patch("app.services.shared.spec._save_event", new=AsyncMock()) as save_event_mock:
            await upsert_engine_spec(spec, ctx=spec_ctx)

        spec_ctx.specs.upsert.assert_awaited_once_with(spec)
        save_event_mock.assert_awaited_once_with(spec)


class TestRemoveEngineSpec:
    @pytest.mark.asyncio
    async def test_deletes_spec_and_saves_event(self, spec_ctx: MagicMock):
        spec = EngineSpec(
            engine_id=uuid4(),
            config={"mode": "proxy"},
            enabled=False,
            generation=7,
        )

        with patch("app.services.shared.spec._save_event", new=AsyncMock()) as save_event_mock:
            await remove_engine_spec(spec, ctx=spec_ctx)

        spec_ctx.specs.delete_by_engine.assert_awaited_once_with(spec.engine_id)
        save_event_mock.assert_awaited_once_with(spec)
