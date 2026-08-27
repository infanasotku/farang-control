from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domains.state import InstancePhase


class ApplyHeartbeatCmd(BaseModel):
    engine_id: UUID
    instance_id: UUID

    epoch: int
    seq_no: int
    phase: InstancePhase
    generation: int


class ReplacementPermit(BaseModel):
    engine_id: UUID
    current_instance_id: UUID
    permit: str
    expires_at: datetime
