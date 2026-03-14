from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.domains.engine import EngineSpec

STALE_THRESHOLD = timedelta(seconds=30)
DEAD_THRESHOLD = timedelta(minutes=5)


class LivenessStatus(StrEnum):
    ALIVE = "alive"
    STALE = "stale"
    DEAD = "dead"


class ReportedPhase(StrEnum):
    STARTING = "starting"


@dataclass
class EngineRuntimeState:
    engine_id: UUID

    reported_phase: ReportedPhase
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int

    def get_liveness(self, now: datetime) -> LivenessStatus:
        if now - self.last_seen_at > DEAD_THRESHOLD:
            liveness = LivenessStatus.DEAD
        elif now - self.last_seen_at > STALE_THRESHOLD:
            liveness = LivenessStatus.STALE
        else:
            liveness = LivenessStatus.ALIVE

        return liveness


@dataclass
class NewEngineRuntimeState:
    engine_id: UUID

    reported_phase: str
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int


class SyncStatus(StrEnum):
    IN_SYNC = "in_sync"
    OUTDATED = "outdated"


@dataclass
class DerivedEngineStatus:
    liveness: LivenessStatus
    sync: SyncStatus

    @classmethod
    def derive(cls, now: datetime, *, spec: EngineSpec, runtime: EngineRuntimeState) -> "DerivedEngineStatus":
        sync = SyncStatus.IN_SYNC if runtime.observed_generation == spec.generation else SyncStatus.OUTDATED

        return cls(liveness=runtime.get_liveness(now), sync=sync)


@dataclass
class EngineInstance:
    instance_id: UUID
    engine_id: UUID
    epoch: int
    created_at: datetime
