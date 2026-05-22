from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domains.state import InstancePhase, LivenessStatus, SyncStatus


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


class DerivedProjection(Projection):
    model_config = ConfigDict(from_attributes=True)

    liveness: LivenessStatus | None = None


class StartSyncAllProjectionsCmd(BaseModel):
    correlation_id: str


class SyncAllProjectionsCmd(BaseModel):
    lock_token: str
