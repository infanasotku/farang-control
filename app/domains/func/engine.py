from dataclasses import dataclass
from uuid import UUID

from app.domains.engine import Engine, EngineSpec
from app.services.exceptions.engine import EngineNotFoundError


@dataclass
class CreationResult:
    engine: Engine
    spec: EngineSpec


def create_engine(name: str) -> CreationResult:
    engine = Engine.create(name=name)
    spec = EngineSpec.initial(engine.id)

    return CreationResult(engine=engine, spec=spec)


@dataclass
class RemovalResult:
    engine_to_remove: Engine
    spec_to_remove: EngineSpec | None


def remove_engine(
    engine_id: UUID,
    *,
    engine: Engine | None,
    spec: EngineSpec | None,
) -> RemovalResult:
    if engine is None:
        raise EngineNotFoundError(engine_id)

    return RemovalResult(
        engine_to_remove=engine,
        spec_to_remove=spec,
    )
