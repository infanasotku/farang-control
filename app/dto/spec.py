from uuid import UUID

from pydantic import BaseModel


class UpdateSpecCmd(BaseModel):
    engine_id: UUID

    config: dict | None = None
    enabled: bool | None = None
