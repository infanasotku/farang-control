from celery import Celery, signals

from app.container import Container
from app.controllers.tasks.runtime import create_runtime, stop_runtime
from app.infra.logging import create_logger, logger

create_logger(with_process_name=True)


@signals.setup_logging.connect()
def setup_celery_logging(**kwargs):
    pass


def create_app():
    logger.info("Creating worker application")
    container = Container()
    settings = container.settings()

    app = Celery(
        "control-worker",
        broker=str(settings.rabbitmq.dsn),
        backend=str(settings.redis.dsn),
        worker_hijack_root_logger=False,
    )

    @signals.worker_process_init.connect(weak=False)
    def on_worker_process_init(**kwargs):
        container = Container()

        create_runtime(container)

    @signals.worker_process_shutdown.connect(weak=False)
    def on_worker_process_shutdown(**kwargs):
        stop_runtime()

    logger.info("Worker application created")
    return app


app = create_app()
