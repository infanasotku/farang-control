from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domains.state import InstancePhase, SyncStatus


class UpsertProjection(BaseModel):
    engine_id: UUID

    name: str
    config: dict
    enabled: bool
    phase: InstancePhase | None
    last_seen_at: datetime | None
    sync: SyncStatus | None


class Projection(BaseModel):
    engine_id: UUID

    name: str
    config: dict
    enabled: bool
    phase: InstancePhase | None = None
    last_seen_at: datetime | None = None
    sync: SyncStatus | None = None
