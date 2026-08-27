from datetime import datetime
from uuid import UUID

from pydantic.dataclasses import dataclass

from app.domains.exceptions.state import CurrentInstanceAliveError, InstanceDeprecatedError
from app.domains.state import EngineInstance, EngineRuntimeState, LivenessStatus


@dataclass
class RegistrationResult:
    epoch: int
    new_instance: EngineInstance | None
    new_runtime_state: EngineRuntimeState | None


def decide_registration(
    *,
    now: datetime,
    engine_id: UUID,
    requested_instance_id: UUID,
    current_state: EngineRuntimeState | None,
    existing_instance: EngineInstance | None,
    replacement_permit_digest: bytes | None = None,
) -> RegistrationResult:
    """
    Raises:
        InstanceDeprecatedError: if the requested instance ID is different from the current one but an instance with the requested ID already exists.
        CurrentInstanceAliveError: if the current instance is still alive (not DEAD) and a new instance is being requested.
    """
    if existing_instance is not None:
        if current_state is None:
            raise RuntimeError("Inconsistent state: instance exists but state does not exist")

        if existing_instance.instance_id == current_state.current_instance_id:
            return RegistrationResult(
                epoch=current_state.current_epoch,
                new_instance=None,
                new_runtime_state=None,
            )

        raise InstanceDeprecatedError(requested_instance_id)

    if (
        current_state is not None
        and current_state.get_liveness(now) != LivenessStatus.DEAD
        and not current_state.accepts_replacement_permit(now=now, digest=replacement_permit_digest)
    ):
        raise CurrentInstanceAliveError(current_state.current_instance_id)

    epoch = 1 if current_state is None else current_state.current_epoch + 1

    instance = EngineInstance.create(
        now=now,
        instance_id=requested_instance_id,
        engine_id=engine_id,
        epoch=epoch,
    )
    runtime_state = EngineRuntimeState.initial(
        now=now,
        engine_id=engine_id,
        instance_id=requested_instance_id,
        epoch=epoch,
    )

    return RegistrationResult(
        epoch=epoch,
        new_instance=instance,
        new_runtime_state=runtime_state,
    )
