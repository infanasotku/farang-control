from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class EngineRuntimeState:
    id: int

    engine_id: UUID

    reported_phase: str
    observed_generation: int

    last_seen_at: datetime
