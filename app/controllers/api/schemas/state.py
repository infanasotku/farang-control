from uuid import UUID

from pydantic import BaseModel

from app.domains.state import InstancePhase


class HeartbeatRequest(BaseModel):
    instance_id: UUID

    epoch: int
    seq_no: int
    phase: InstancePhase
    generation: int
