from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.base import Base, intpk, uuidpk


class EngineInstance(Base):
    __tablename__ = "engine_instances"

    id: Mapped[uuidpk]
    engine_id: Mapped[UUID] = mapped_column(ForeignKey("engines.id", ondelete="CASCADE"), nullable=False)

    epoch: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("engine_id", "epoch", name="uq_engine_instance_engine_id_epoch"),
        UniqueConstraint("id", "engine_id", name="uq_engine_instance_id_engine_id"),
    )


class EngineRuntimeState(Base):
    __tablename__ = "engine_runtime_states"

    id: Mapped[intpk]
    reported_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    observed_generation: Mapped[int] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    engine_id: Mapped[UUID] = mapped_column(ForeignKey("engines.id", ondelete="CASCADE"), nullable=False)
    current_instance_id: Mapped[UUID] = mapped_column(
        ForeignKey("engine_instances.id", ondelete="SET NULL"), nullable=True
    )
    current_epoch: Mapped[int] = mapped_column(nullable=True)
    last_seq_no: Mapped[int] = mapped_column(nullable=False)
