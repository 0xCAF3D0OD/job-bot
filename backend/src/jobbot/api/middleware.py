"""Identifiant de requête, journal d'accès et métriques HTTP.

Le journal et les métriques utilisent le modèle de route (/api/offers/{id}), jamais l'URL
réelle ni la chaîne de requête : nombre d'étiquettes borné et aucune donnée dans les logs.
"""

import logging
import re
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from jobbot.log import get_logger
from jobbot.metrics import HTTP_DURATION, HTTP_REQUESTS

log = get_logger("jobbot.access")

REQUEST_ID_HEADER = "X-Request-ID"
# Les sondes et le scraping Prometheus ne sont journalisés qu'en DEBUG.
QUIET_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "unmatched"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        started = time.perf_counter()
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            status = 500
            try:
                response = await call_next(request)
                status = response.status_code
            finally:
                duration = time.perf_counter() - started
                route = _route_template(request)
                HTTP_REQUESTS.labels(request.method, route, str(status)).inc()
                HTTP_DURATION.labels(request.method, route).observe(duration)
                level = logging.DEBUG if request.url.path in QUIET_PATHS else logging.INFO
                log.log(
                    level,
                    "http_request",
                    method=request.method,
                    route=route,
                    status=status,
                    duration_ms=round(duration * 1000, 1),
                )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
