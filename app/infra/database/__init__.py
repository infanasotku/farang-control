from sqlalchemy.ext.asyncio import create_async_engine

from app.infra.config.postgres import PostgreSQLSettings


def create_engine(settings: PostgreSQLSettings, *, tx: bool = False):
    return create_async_engine(
        settings.dsn,
        connect_args=dict(server_settings=dict(search_path=settings.schema)),
        pool_pre_ping=False,
        pool_recycle=3600,
        isolation_level="AUTOCOMMIT" if not tx else None,
    )
