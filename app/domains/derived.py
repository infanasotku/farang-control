from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domains.runtime import EngineRuntimeState, LivenessStatus
from app.domains.spec import EngineSpec


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
