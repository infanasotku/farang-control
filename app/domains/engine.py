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
        return self._calc_config_hash(self.config)

    @staticmethod
    def _calc_config_hash(config: dict) -> str:
        dump = json.dumps(config, sort_keys=True)
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
        new_config = self.config if config is None else config
        new_enabled = self.enabled if enabled is None else enabled

        changed = new_enabled != self.enabled or self._calc_config_hash(new_config) != self.config_hash

        self.config = new_config
        self.enabled = new_enabled

        if changed:
            self.generation += 1
