from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateEngineInstance(BaseModel):
    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int
    created_at: datetime
