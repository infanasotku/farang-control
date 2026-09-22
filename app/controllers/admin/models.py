from sqlalchemy import JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domains.state import InstancePhase, LivenessStatus, SyncStatus
from app.dto.engine_status import EngineStatus
from app.infra.postgres.models.base import uuidpk


class Base(DeclarativeBase): ...


class EngineProjection(Base):
    """Presentation-only model; the legacy name preserves existing admin URLs.

    No projection table or cache is queried. EngineService supplies live SQL data.
    """

    __tablename__ = "engine_projections"

    engine_id: Mapped[uuidpk]

    name: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)

    phase: Mapped[InstancePhase] = mapped_column(String(20), nullable=True)
    sync: Mapped[SyncStatus] = mapped_column(String(20), nullable=True)
    liveness: Mapped[LivenessStatus] = mapped_column(String(20), nullable=True)

    @classmethod
    def from_status(cls, status: EngineStatus) -> "EngineProjection":
        return cls(
            engine_id=status.engine_id,
            name=status.name,
            config=status.config,
            enabled=status.enabled,
            phase=status.phase,
            sync=status.sync,
            liveness=status.liveness,
        )
