from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class NewEngineRuntimeState:
    engine_id: UUID

    reported_phase: str
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int


@dataclass
class EngineRuntimeState:
    id: int

    engine_id: UUID

    reported_phase: str
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int
