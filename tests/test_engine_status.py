from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine, delete, update
from sqlalchemy.orm import Session

from app.domains.engine import Engine, EngineSpec
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.state import EngineRuntimeState, InstancePhase, LivenessStatus, SyncStatus
from app.dto.engine_status import EngineStatusSource
from app.infra.postgres.models.base import Base
from app.infra.postgres.models.engine import Engine as EngineModel
from app.infra.postgres.models.engine import EngineSpec as EngineSpecModel
from app.infra.postgres.models.state import EngineInstance as EngineInstanceModel
from app.infra.postgres.models.state import EngineRuntimeState as RuntimeModel
from app.infra.postgres.repositories.engine_status import PgEngineStatusRepository
from app.services.engine import EngineService

NOW = datetime(2026, 9, 22, tzinfo=timezone.utc)


@pytest.fixture
def source():
    engine_id = uuid4()
    return EngineStatusSource(
        engine=Engine(id=engine_id, name="edge"),
        spec=EngineSpec(engine_id=engine_id, config={"inbounds": []}, enabled=True, generation=7),
        runtime=EngineRuntimeState(
            engine_id=engine_id,
            reported_phase=InstancePhase.RUNNING,
            observed_generation=7,
            last_seen_at=NOW,
            last_seq_no=1,
            current_instance_id=uuid4(),
            current_epoch=1,
        ),
    )


@pytest.fixture
def status_ctx(uow):
    ctx = MagicMock()
    ctx.statuses.get_by_id = AsyncMock(return_value=None)
    ctx.statuses.get = AsyncMock(return_value=[])
    ctx.statuses.count = AsyncMock(return_value=0)
    uow.begin.return_value.__aenter__.return_value = ctx
    return ctx


@pytest.mark.asyncio
async def test_status_is_recomputed_after_spec_and_heartbeat_changes(uow, status_ctx, source):
    status_ctx.statuses.get_by_id.return_value = source
    service = EngineService(uow)
    with patch("app.services.engine.now_utc", return_value=NOW):
        current = await service.get_status(source.engine.id)
        assert current.sync == SyncStatus.IN_SYNC
        assert current.liveness == LivenessStatus.ALIVE

        source.engine.name = "renamed"
        source.spec.generation += 1
        source.spec.config = {"updated": True}
        source.spec.enabled = False
        changed = await service.get_status(source.engine.id)
        assert changed.name == "renamed"
        assert changed.config == {"updated": True}
        assert changed.enabled is False
        assert changed.sync == SyncStatus.OUTDATED

        source.runtime.observed_generation = source.spec.generation
        source.runtime.reported_phase = InstancePhase.IDLE
        applied = await service.get_status(source.engine.id)
        assert applied.sync == SyncStatus.IN_SYNC
        assert applied.phase == InstancePhase.IDLE


@pytest.mark.asyncio
async def test_liveness_changes_without_a_write(uow, status_ctx, source):
    status_ctx.statuses.get_by_id.return_value = source
    service = EngineService(uow)
    for seconds, expected in ((0, LivenessStatus.ALIVE), (11, LivenessStatus.STALE), (31, LivenessStatus.DEAD)):
        with patch("app.services.engine.now_utc", return_value=NOW + timedelta(seconds=seconds)):
            assert (await service.get_status(source.engine.id)).liveness == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_spec,missing_runtime", [(True, True), (False, True), (True, False)])
async def test_engine_remains_visible_without_spec_or_runtime(uow, status_ctx, source, missing_spec, missing_runtime):
    if missing_spec:
        source.spec = None
    if missing_runtime:
        source.runtime = None
    status_ctx.statuses.get_by_id.return_value = source
    with patch("app.services.engine.now_utc", return_value=NOW):
        result = await EngineService(uow).get_status(source.engine.id)
    assert result.engine_id == source.engine.id
    assert result.sync is None
    if missing_spec:
        assert result.config == {}
        assert result.enabled is False
    if missing_runtime:
        assert result.phase is None
        assert result.liveness is None
        assert result.last_seen_at is None
    else:
        assert result.phase == InstancePhase.RUNNING
        assert result.liveness == LivenessStatus.ALIVE


@pytest.mark.asyncio
async def test_missing_engine_raises(uow, status_ctx):
    with pytest.raises(EngineNotFoundError):
        await EngineService(uow).get_status(uuid4())


@pytest.mark.asyncio
async def test_page_reports_total_even_beyond_last_page(uow, status_ctx):
    status_ctx.statuses.count.return_value = 25
    page = await EngineService(uow).get_statuses(offset=30, limit=10)
    assert page.items == []
    assert page.total == 25
    status_ctx.statuses.get.assert_awaited_once_with(offset=30, limit=10)
    uow.begin.assert_called_once_with(write=False)


@pytest.fixture
def status_database():
    # Execute the actual ORM joins against SQLite; only the async boundary is adapted.
    # PostgreSQL-specific transactions and timezone behavior are outside this test.
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        adapter = MagicMock()
        adapter.execute = AsyncMock(side_effect=session.execute)
        adapter.scalar = AsyncMock(side_effect=session.scalar)
        yield session, PgEngineStatusRepository(adapter), adapter
    engine.dispose()


@pytest.mark.asyncio
async def test_sql_reads_fresh_values_and_missing_engine(status_database):
    session, repo, adapter = status_database
    engine_id, instance_id = uuid4(), uuid4()
    session.add(EngineModel(id=engine_id, name="edge"))
    session.add(EngineSpecModel(engine_id=engine_id, config={"old": True}, enabled=True, generation=7))
    session.add(EngineInstanceModel(id=instance_id, engine_id=engine_id, epoch=1, created_at=NOW))
    session.add(
        RuntimeModel(
            engine_id=engine_id,
            current_instance_id=instance_id,
            current_epoch=1,
            reported_phase=InstancePhase.RUNNING,
            observed_generation=7,
            last_seen_at=NOW,
            last_seq_no=1,
        )
    )
    session.commit()

    result = await repo.get_by_id(engine_id)
    assert result.spec.config == {"old": True}
    assert result.runtime.observed_generation == 7
    adapter.execute.assert_awaited_once()

    session.execute(update(EngineSpecModel).values(config={"new": True}, generation=8))
    session.execute(update(RuntimeModel).values(observed_generation=8, reported_phase=InstancePhase.FAILED))
    session.commit()
    result = await repo.get_by_id(engine_id)
    assert result.spec.config == {"new": True}
    assert result.spec.generation == 8
    assert result.runtime.observed_generation == 8
    assert result.runtime.reported_phase == InstancePhase.FAILED

    session.execute(delete(RuntimeModel))
    session.execute(delete(EngineSpecModel))
    session.execute(delete(EngineInstanceModel))
    session.execute(delete(EngineModel))
    session.commit()
    assert await repo.get_by_id(engine_id) is None
    assert await repo.count() == 0


@pytest.mark.asyncio
async def test_sql_outer_joins_and_deterministic_pagination(status_database):
    session, repo, adapter = status_database
    ids = [UUID(f"00000000-aaaa-4000-8000-{i:012x}") for i in range(1, 5)]
    session.add_all([EngineModel(id=i, name="same-name") for i in reversed(ids)])
    session.add(EngineSpecModel(engine_id=ids[1], config={"present": True}, enabled=True, generation=1))
    session.commit()

    first = await repo.get(offset=0, limit=2)
    second = await repo.get(offset=2, limit=2)
    assert [item.engine.id for item in first + second] == ids
    assert first[0].spec is None
    assert first[1].spec.config == {"present": True}
    assert all(item.runtime is None for item in first + second)
    assert await repo.get(offset=4, limit=2) == []
    assert await repo.count() == 4
    assert adapter.execute.await_count == 3
