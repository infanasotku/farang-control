import logging
import uuid

from starlette.responses import JSONResponse

from app.infra.common.correlation import RequestContext, with_request_context

CORRELATION_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


class CorrelationIdASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = str(uuid.uuid4())

        response_started = False
        response_completed = False

        async def send_wrapper(message):
            nonlocal response_started, response_completed
            if message["type"] == "http.response.start":
                response_started = True
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                response_completed = True
            await send(message)

        with with_request_context(RequestContext(request_id=request_id)):
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception:
                logger.exception("Unhandled exception while handling request")

                if response_started or response_completed:
                    return

                resp = JSONResponse(
                    {
                        "detail": "Internal Server Error",
                        CORRELATION_ID_HEADER: request_id,
                    },
                    status_code=500,
                )
                await resp(scope, receive, send)
                return
