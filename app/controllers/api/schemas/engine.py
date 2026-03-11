from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EngineSpecResponse(BaseModel):
    engine_id: UUID
    config: dict
    enabled: bool

    config_hash: str

    model_config = ConfigDict(from_attributes=True)
