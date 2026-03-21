import hashlib
import json
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Engine:
    id: UUID
    name: str

    @classmethod
    def create(cls, name: str) -> "Engine":
        return cls(id=uuid4(), name=name)


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

    @classmethod
    def initial(cls, engine_id: UUID) -> "EngineSpec":
        return cls(
            engine_id=engine_id,
            config={},
            enabled=False,
            generation=0,
        )

    def update(self, *, config: dict | None = None, enabled: bool | None = None) -> None:
        if config is not None:
            self.config = config
        if enabled is not None:
            self.enabled = enabled
        self.generation += 1
