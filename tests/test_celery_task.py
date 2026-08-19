import asyncio
from unittest.mock import MagicMock, patch

from app.infra.celery.task import async_task


def test_async_task_runs_coroutine_on_worker_runtime():
    runtime = MagicMock()

    @async_task
    async def example_task(value: int) -> int:
        return value + 1

    runtime.run.side_effect = asyncio.run

    with patch("app.infra.celery.runtime.get_runtime", return_value=runtime):
        result = example_task.run(41)

    assert result == 42
    runtime.run.assert_called_once()
