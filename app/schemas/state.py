from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EngineInstance(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int


class CreateEngineInstance(BaseModel):
    id_: UUID = Field(alias="id", serialization_alias="id")
    engine_id: UUID
    epoch: int
