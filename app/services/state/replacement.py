import secrets
from uuid import UUID

from app.contracts.uow import UnitOfWork
from app.domains.exceptions.engine import EngineNotFoundError
from app.domains.exceptions.state import EngineHasNoRuntimeStateError
from app.dto.state import ReplacementPermit
from app.infra.common.time import now_utc
from app.infra.logging.logger import get_logger
from app.infra.postgres.uows.state import StateReadContext, StateWriteContext
from app.services.state.shared import (
    REPLACEMENT_PERMIT_RANDOM_BYTES,
    REPLACEMENT_PERMIT_TTL,
    digest_replacement_permit,
)

logger = get_logger().getChild(__name__)


class IssueReplacementPermitUC:
    def __init__(self, *, uow: UnitOfWork[StateReadContext, StateWriteContext]) -> None:
        self._uow = uow

    async def run(self, *, engine_id: UUID) -> ReplacementPermit:
        logger.info(f"Issuing replacement permit: engine_id={engine_id}")
        async with self._uow.begin(write=True) as ctx:
            engine = await ctx.engines.get_engine_for_update(engine_id)
            if engine is None:
                logger.warning(f"Issue replacement permit failed because engine was not found: engine_id={engine_id}")
                raise EngineNotFoundError(engine_id)

            state = await ctx.states.get_engine_state_for_update(engine_id)
            if state is None:
                logger.warning(
                    f"Issue replacement permit failed because engine has no runtime owner: engine_id={engine_id}"
                )
                raise EngineHasNoRuntimeStateError(engine_id)

            now = now_utc()
            permit = secrets.token_urlsafe(REPLACEMENT_PERMIT_RANDOM_BYTES)
            expires_at = now + REPLACEMENT_PERMIT_TTL
            state.issue_replacement_permit(
                digest=digest_replacement_permit(permit),
                expires_at=expires_at,
            )
            await ctx.states.upsert_engine_state(state)

        logger.info(
            f"Replacement permit issued: engine_id={engine_id} current_instance_id={state.current_instance_id} expires_at={expires_at.isoformat()}"
        )
        return ReplacementPermit(
            engine_id=engine_id,
            current_instance_id=state.current_instance_id,
            permit=permit,
            expires_at=expires_at,
        )


class RevokeReplacementPermitUC:
    def __init__(self, *, uow: UnitOfWork[StateReadContext, StateWriteContext]) -> None:
        self._uow = uow

    async def run(self, *, engine_id: UUID) -> None:
        logger.info(f"Revoking replacement permit: engine_id={engine_id}")
        async with self._uow.begin(write=True) as ctx:
            engine = await ctx.engines.get_engine_for_update(engine_id)
            if engine is None:
                logger.warning(f"Revoke replacement permit failed because engine was not found: engine_id={engine_id}")
                raise EngineNotFoundError(engine_id)

            state = await ctx.states.get_engine_state_for_update(engine_id)
            if state is None:
                logger.warning(
                    f"Revoke replacement permit failed because engine has no runtime owner: engine_id={engine_id}"
                )
                raise EngineHasNoRuntimeStateError(engine_id)

            state.revoke_replacement_permit()
            await ctx.states.upsert_engine_state(state)

        logger.info(f"Replacement permit revoked: engine_id={engine_id}")
