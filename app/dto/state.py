from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.infra.common.time import now_utc


class EngineInstance(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int
    created_at: datetime


class CreateEngineInstance(BaseModel):
    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int
    created_at: datetime = Field(default_factory=now_utc)
