from dataclasses import dataclass
from uuid import UUID


@dataclass
class Engine:
    id: UUID
    name: str
