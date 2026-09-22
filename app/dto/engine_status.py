from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domains.engine import Engine, EngineSpec
from app.domains.state import DerivedEngineStatus, EngineRuntimeState, InstancePhase, LivenessStatus, SyncStatus


@dataclass
class EngineStatusSource:
    engine: Engine
    spec: EngineSpec | None
    runtime: EngineRuntimeState | None


class EngineStatus(BaseModel):
    engine_id: UUID
    name: str
    config: dict
    enabled: bool
    phase: InstancePhase | None = None
    last_seen_at: datetime | None = None
    sync: SyncStatus | None = None
    liveness: LivenessStatus | None = None

    @classmethod
    def derive(cls, source: EngineStatusSource, *, now: datetime) -> "EngineStatus":
        engine, spec, runtime = source.engine, source.spec, source.runtime
        return cls(
            engine_id=engine.id,
            name=engine.name,
            config=spec.config if spec else {},
            enabled=spec.enabled if spec else False,
            phase=runtime.reported_phase if runtime else None,
            last_seen_at=runtime.last_seen_at if runtime else None,
            sync=DerivedEngineStatus.derive(now, spec=spec, runtime=runtime).sync if spec and runtime else None,
            liveness=runtime.get_liveness(now) if runtime else None,
        )


class EngineStatusPage(BaseModel):
    items: list[EngineStatus]
    total: int
