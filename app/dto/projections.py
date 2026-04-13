from uuid import UUID

from pydantic import BaseModel

from app.domains.state import InstancePhase


class UpsertProjection(BaseModel):
    engine_id: UUID

    name: str | None = None
    config: dict | None = None
    enabled: bool | None = None
    phase: InstancePhase | None = None
