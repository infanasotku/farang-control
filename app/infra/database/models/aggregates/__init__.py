from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.base import Base, uuidpk


class EngineAggregate(Base):
    __tablename__ = "engine_aggregates"

    engine_id: Mapped[uuidpk]

    name: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)
    phase: Mapped[str] = mapped_column(String(20), nullable=False)
