from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from app.infra.common.correlation import RequestContext, with_request_context
from app.infra.logging import logger
from celery import Task, shared_task


def as_task(func) -> Task:
    return func


def async_task(func: Callable[..., Coroutine[Any, Any, Any]]) -> Task:
    """Expose an async function as a Celery task using the worker event loop."""

    @shared_task(name=f"{func.__module__}.{func.__name__}")
    @wraps(func)
    def wrapper(*args, **kwargs):
        from app.infra.celery.runtime import get_runtime

        return get_runtime().run(func(*args, **kwargs))

    return as_task(wrapper)


class BaseTask(Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        with with_request_context(RequestContext(request_id=self.request.id)):
            logger.info(
                "Task is starting",
                extra={
                    "task_id": self.request.id,
                    "task_name": self.name,
                },
            )

            try:
                return super().__call__(*args, **kwargs)
            except Exception:
                logger.exception(
                    "Task failed",
                    extra={
                        "task_id": self.request.id,
                        "task_name": self.name,
                    },
                )
                raise
            finally:
                logger.info(
                    "Task finished",
                    extra={
                        "task_id": self.request.id,
                        "task_name": self.name,
                    },
                )
