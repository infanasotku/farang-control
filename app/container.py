from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infra.cache import create_redis_context
from app.infra.cache.repositories.projections import RedisEngineProjectionRepository
from app.infra.config import generate_settings
from app.infra.database import create_engine
from app.infra.database.uows import PgEngineSpecUnitOfWork, PgEngineUnitOfWork
from app.infra.database.uows.projections import PgProjectionUnitOfWork
from app.infra.database.uows.state import PgStateUnitOfWork
from app.services.engine import EngineService
from app.services.projections.engine import EngineProjectionService
from app.services.spec import SpecService
from app.services.state import StateService


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(generate_settings)
    auth_settings = settings.provided.auth

    # Redis
    redis = providers.Resource(
        create_redis_context,
        settings.provided.redis,
    )

    projection_repo = providers.Factory(RedisEngineProjectionRepository, redis)
    #

    # Postgres
    read_engine = providers.Singleton(create_engine, settings.provided.postgres, tx=False)
    write_engine = providers.Singleton(create_engine, settings.provided.postgres, tx=True)
    read_sessionmaker = providers.Singleton(async_sessionmaker[AsyncSession], read_engine)
    write_sessionmaker = providers.Singleton(async_sessionmaker[AsyncSession], write_engine)

    engine_uow = providers.Factory(
        PgEngineUnitOfWork,
        read_sessionmaker=read_sessionmaker,
        write_sessionmaker=write_sessionmaker,
    )
    state_uow = providers.Factory(
        PgStateUnitOfWork,
        read_sessionmaker=read_sessionmaker,
        write_sessionmaker=write_sessionmaker,
    )
    spec_uow = providers.Factory(
        PgEngineSpecUnitOfWork,
        read_sessionmaker=read_sessionmaker,
        write_sessionmaker=write_sessionmaker,
    )
    projection_uow = providers.Factory(
        PgProjectionUnitOfWork,
        read_sessionmaker=read_sessionmaker,
        write_sessionmaker=write_sessionmaker,
    )
    #

    projection_service = providers.Factory(EngineProjectionService, projection_repo)
    engine_service = providers.Factory(EngineService, engine_uow, projection=projection_service)
    state_service = providers.Factory(StateService, state_uow, projection=projection_service)
    spec_service = providers.Factory(SpecService, spec_uow, projection=projection_service)
