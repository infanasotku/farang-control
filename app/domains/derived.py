from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from app.domains.runtime import EngineRuntimeState
from app.domains.spec import EngineSpec
from app.infra.common.time import now_utc


class LivenessStatus(StrEnum):
    ALIVE = "alive"
    STALE = "stale"
    DEAD = "dead"


class SyncStatus(StrEnum):
    IN_SYNC = "in_sync"
    OUTDATED = "outdated"


STALE_THRESHOLD = timedelta(seconds=30)
DEAD_THRESHOLD = timedelta(minutes=5)


@dataclass
class DerivedEngineStatus:
    liveness: LivenessStatus
    sync: SyncStatus

    @classmethod
    def derive(cls, *, spec: EngineSpec, runtime: EngineRuntimeState) -> "DerivedEngineStatus":
        if now_utc() - runtime.last_seen_at > DEAD_THRESHOLD:
            liveness = LivenessStatus.DEAD
        elif now_utc() - runtime.last_seen_at > STALE_THRESHOLD:
            liveness = LivenessStatus.STALE
        else:
            liveness = LivenessStatus.ALIVE

        sync = SyncStatus.IN_SYNC if runtime.observed_generation == spec.generation else SyncStatus.OUTDATED

        return cls(liveness=liveness, sync=sync)
