from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.base import Base, intpk, uuidpk


class Engine(Base):
    __tablename__ = "engines"

    id: Mapped[uuidpk]
    name: Mapped[str] = mapped_column(String(20), nullable=False)


class EngineSpec(Base):
    __tablename__ = "engine_specs"

    id: Mapped[intpk]
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)
    generation: Mapped[int] = mapped_column(nullable=False)

    engine_id: Mapped[UUID] = mapped_column(
        ForeignKey("engines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
