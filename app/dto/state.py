from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateEngineInstance(BaseModel):
    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int
    created_at: datetime


class CreateEngineRuntimeState(BaseModel):
    engine_id: UUID

    reported_phase: str
    observed_generation: int
    last_seen_at: datetime
    last_seq_no: int

    current_instance_id: UUID
    current_epoch: int
