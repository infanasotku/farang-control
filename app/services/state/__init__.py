from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.dto.state import ApplyHeartbeatCmd, ReplacementPermit
from app.infra.postgres.uows.state import StateReadContext, StateWriteContext
from app.services.projections.engine import EngineProjectionService
from app.services.state.heartbeat import ApplyHeartbeatUC
from app.services.state.registration import RegisterInstanceUC
from app.services.state.replacement import IssueReplacementPermitUC, RevokeReplacementPermitUC


class StateService:
    def __init__(
        self, uow: UnitOfWork[StateReadContext, StateWriteContext], *, projection: EngineProjectionService
    ) -> None:
        self._uow = uow
        self._projection = projection

    async def register_instance(
        self,
        *,
        instance_id: UUID,
        engine_id: UUID,
        replacement_permit: str | None = None,
    ) -> int:
        return await RegisterInstanceUC(
            uow=self._uow,
            projection=self._projection,
        ).run(
            instance_id=instance_id,
            engine_id=engine_id,
            replacement_permit=replacement_permit,
        )

    async def apply_heartbeat(self, cmd: ApplyHeartbeatCmd) -> None:
        return await ApplyHeartbeatUC(
            uow=self._uow,
            projection=self._projection,
        ).run(cmd)

    async def issue_replacement_permit(self, *, engine_id: UUID) -> ReplacementPermit:
        return await IssueReplacementPermitUC(uow=self._uow).run(engine_id=engine_id)

    async def revoke_replacement_permit(self, *, engine_id: UUID) -> None:
        return await RevokeReplacementPermitUC(uow=self._uow).run(engine_id=engine_id)
