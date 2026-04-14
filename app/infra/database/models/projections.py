from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domains.state import InstancePhase, SyncStatus
from app.infra.database.models.base import Base, uuidpk


class EngineProjection(Base):
    __tablename__ = "engine_projections"

    engine_id: Mapped[uuidpk]

    name: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)

    phase: Mapped[InstancePhase] = mapped_column(String(20), nullable=True)
    sync: Mapped[SyncStatus] = mapped_column(String(20), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
