"""Request ID middleware.

Injects a correlation ID into every request/response cycle:
- Reads X-Request-ID from incoming request headers (pass-through for upstream tracers)
- Generates a new UUID4 if absent or if the value is invalid (> 128 chars / non-ASCII)
- Adds the correlation ID to the response as X-Request-ID

Use in logs:
    request_id = request.headers.get("x-request-id", "unknown")
    logger.info("Processing...", request_id=request_id)
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_MAX_ID_LEN = 128


def _get_or_generate_request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "")
    # Accept client-supplied ID only if safe (ASCII, bounded length)
    if incoming and len(incoming) <= _MAX_ID_LEN and incoming.isascii():
        return incoming
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _get_or_generate_request_id(request)
        # Expose to downstream handlers via request state
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
