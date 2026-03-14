from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EngineSpecResponse(BaseModel):
    engine_id: UUID
    config: dict
    enabled: bool

    generation: int
    config_hash: str

    model_config = ConfigDict(from_attributes=True)


class RegisterEngineInstanceResponse(BaseModel):
    epoch: int
