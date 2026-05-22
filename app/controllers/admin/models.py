from sqlalchemy import JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domains.state import InstancePhase, LivenessStatus, SyncStatus
from app.infra.database.models.base import uuidpk


class Base(DeclarativeBase): ...


class EngineProjection(Base):
    __tablename__ = "engine_projections"

    engine_id: Mapped[uuidpk]

    name: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)

    phase: Mapped[InstancePhase] = mapped_column(String(20), nullable=True)
    sync: Mapped[SyncStatus] = mapped_column(String(20), nullable=True)
    liveness: Mapped[LivenessStatus] = mapped_column(String(20), nullable=True)
