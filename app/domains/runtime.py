from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.infra.common.time import now_utc


@dataclass
class NewEngineRuntimeState:
    engine_id: UUID

    reported_phase: str
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int


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
    id: int

    engine_id: UUID

    reported_phase: ReportedPhase
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int

    def get_liveness(self) -> LivenessStatus:
        if now_utc() - self.last_seen_at > DEAD_THRESHOLD:
            liveness = LivenessStatus.DEAD
        elif now_utc() - self.last_seen_at > STALE_THRESHOLD:
            liveness = LivenessStatus.STALE
        else:
            liveness = LivenessStatus.ALIVE

        return liveness
