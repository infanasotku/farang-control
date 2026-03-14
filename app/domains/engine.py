import hashlib
import json
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Engine:
    id: UUID
    name: str


@dataclass
class EngineSpec:
    engine_id: UUID
    config: dict  # TODO: make this more specific
    enabled: bool

    generation: int

    @property
    def config_hash(self) -> str:
        dump = json.dumps(self.config, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest()
