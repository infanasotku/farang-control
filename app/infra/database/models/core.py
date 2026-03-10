from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DATETIME, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

uuidpk = Annotated[UUID, mapped_column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)]
intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class Base(DeclarativeBase): ...


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

    engine_id: Mapped[UUID] = mapped_column(ForeignKey("engines.id", ondelete="CASCADE"), nullable=False)


class EngineRuntimeState(Base):
    __tablename__ = "engine_runtime_states"

    id: Mapped[intpk]
    reported_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    observed_generation: Mapped[int] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DATETIME(timezone=True), nullable=False)

    engine_id: Mapped[UUID] = mapped_column(ForeignKey("engines.id", ondelete="CASCADE"), nullable=False)
