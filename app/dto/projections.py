from uuid import UUID

from pydantic import BaseModel

from app.domains.state import InstancePhase


class UpsertProjection(BaseModel):
    engine_id: UUID

    name: str
    config: dict
    enabled: bool
    phase: InstancePhase
