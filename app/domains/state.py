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


class SyncStatus(StrEnum):
    IN_SYNC = "in_sync"
    OUTDATED = "outdated"


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

    @classmethod
    def initial(
        cls,
        *,
        now: datetime,
        engine_id: UUID,
        instance_id: UUID,
        epoch: int,
    ) -> "EngineRuntimeState":
        return cls(
            engine_id=engine_id,
            reported_phase=ReportedPhase.STARTING,
            observed_generation=0,
            last_seen_at=now,
            last_seq_no=0,
            current_instance_id=instance_id,
            current_epoch=epoch,
        )


@dataclass
class EngineInstance:
    instance_id: UUID
    engine_id: UUID
    epoch: int
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        now: datetime,
        instance_id: UUID,
        engine_id: UUID,
        epoch: int,
    ) -> "EngineInstance":
        return cls(
            instance_id=instance_id,
            engine_id=engine_id,
            epoch=epoch,
            created_at=now,
        )


@dataclass
class RegistrationResult:
    epoch: int
    new_instance: EngineInstance | None
    new_runtime_state: EngineRuntimeState | None


@dataclass
class DerivedEngineStatus:
    liveness: LivenessStatus
    sync: SyncStatus

    @classmethod
    def derive(cls, now: datetime, *, spec: EngineSpec, runtime: EngineRuntimeState) -> "DerivedEngineStatus":
        sync = SyncStatus.IN_SYNC if runtime.observed_generation == spec.generation else SyncStatus.OUTDATED

        return cls(liveness=runtime.get_liveness(now), sync=sync)
