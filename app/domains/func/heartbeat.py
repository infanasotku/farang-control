from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domains.exceptions.state import InstanceDeprecatedError, InstanceNotRegisteredError
from app.domains.state import EngineInstance, EngineRuntimeState, InstancePhase


@dataclass
class HeartbeatResult:
    new_state: EngineRuntimeState | None = None


def apply_heartbeat(
    *,
    now: datetime,
    instance_id: UUID,
    state: EngineRuntimeState | None,
    instance: EngineInstance | None,
    # The following fields are from the heartbeat request
    received_epoch: int,
    received_seq_no: int,
    new_phase: InstancePhase,
    new_generation: int,
) -> HeartbeatResult:
    """
    Raises:
        InstanceNotRegisteredError: if the instance is not registered (i.e., state or instance is None).
        InstanceDeprecatedError: if the instance is deprecated (i.e., received_epoch != state.current_epoch).
    """
    result = HeartbeatResult()

    if state is None or instance is None:
        raise InstanceNotRegisteredError(instance_id)

    if received_epoch != state.current_epoch or state.current_instance_id != instance_id:
        raise InstanceDeprecatedError(instance_id)

    if not state.is_new_state(received_seq_no):
        return result

    state.apply_heartbeat(
        now=now,
        reported_phase=new_phase,
        observed_generation=new_generation,
        seq_no=received_seq_no,
    )
    result.new_state = state
    return result
