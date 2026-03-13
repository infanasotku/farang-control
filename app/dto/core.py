from uuid import UUID

from pydantic import BaseModel


class CreateEngine(BaseModel):
    engine_id: UUID
    config: dict
    enabled: bool

    generation: int
