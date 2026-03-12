from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infra.config import generate_settings
from app.infra.database import create_engine
from app.infra.database.uows import PgSpecUnitOfWork
from app.services.engine import EngineService
from app.services.state import StateService


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(generate_settings)

    plain_engine = providers.Singleton(create_engine, settings.provided.postgres, tx=False)
    tx_engine = providers.Singleton(create_engine, settings.provided.postgres, tx=True)

    plain_sessionmaker = providers.Singleton(async_sessionmaker[AsyncSession], plain_engine)
    tx_sessionmaker = providers.Singleton(async_sessionmaker[AsyncSession], tx_engine)

    spec_uow = providers.Factory(
        PgSpecUnitOfWork,
        plain_sessionmaker=plain_sessionmaker,
        tx_sessionmaker=tx_sessionmaker,
    )

    spec_service = providers.Factory(EngineService, spec_uow)
    state_service = providers.Factory(StateService)
