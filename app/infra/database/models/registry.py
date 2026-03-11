from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.base import Base, uuidpk


class EngineInstance(Base):
    __tablename__ = "engine_instances"

    id: Mapped[uuidpk]
    engine_id: Mapped[UUID] = mapped_column(ForeignKey("engines.id", ondelete="CASCADE"), nullable=False)

    epoch: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("engine_id", "epoch", name="uq_engine_instance_engine_id_epoch"),
        UniqueConstraint("id", "engine_id", name="uq_engine_instance_id_engine_id"),
    )
