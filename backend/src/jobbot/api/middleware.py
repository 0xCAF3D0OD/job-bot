"""Identifiant de requête, journal d'accès et métriques HTTP.

Le journal et les métriques utilisent le modèle de route (/api/offers/{id}), jamais l'URL
réelle ni la chaîne de requête : nombre d'étiquettes borné et aucune donnée dans les logs.
"""

import ipaddress
import json
import logging
import re
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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


# Adresses d'exploitation (état détaillé, métriques, version, documentation de l'API) : pour
# l'ordinateur lui-même ou son réseau privé (sonde, Prometheus), jamais au travers d'un
# intermédiaire public (docs/78 §2). /healthz reste ouvert : il ne dit que « ok ».
LOCAL_ONLY = frozenset({"/readyz", "/metrics", "/version", "/api/docs", "/api/openapi.json"})
# Au-delà, la requête est refusée avant d'être lue (le plus gros envoi : un document de 10 Mo).
MAX_BODY = 11 * 1024 * 1024
SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"SAMEORIGIN"),
    (b"referrer-policy", b"same-origin"),
)


def _local(scope: Scope) -> bool:
    headers = {k.lower() for k, _ in scope.get("headers", [])}
    if b"x-forwarded-for" in headers or b"forwarded" in headers:
        return False
    client = scope.get("client")
    try:
        address = ipaddress.ip_address(client[0]) if client else None
    except ValueError:
        return False
    return address is not None and (address.is_loopback or address.is_private)


async def _refuse(send: Send, status: int, detail: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), *SECURITY_HEADERS],
        }
    )
    await send({"type": "http.response.body", "body": json.dumps({"detail": detail}).encode()})


class SecurityMiddleware:
    """En-têtes de sécurité sur chaque réponse, adresses d'exploitation réservées, taille des
    requêtes plafonnée (docs/78 §2)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path", "") in LOCAL_ONLY and not _local(scope):
            await _refuse(send, 404, "Not Found")
            return
        length = dict(scope.get("headers", [])).get(b"content-length")
        if length is not None and (not length.isdigit() or int(length) > MAX_BODY):
            await _refuse(send, 413, "requête trop volumineuse (10 Mo au plus)")
            return
        received = 0

        async def limited() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > MAX_BODY:
                    # Envoi sans taille annoncée qui dépasse : la lecture s'arrête là.
                    return {"type": "http.disconnect"}
            return message

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                present = {k.lower() for k, _ in message.get("headers", [])}
                extra = [(k, v) for k, v in SECURITY_HEADERS if k not in present]
                message["headers"] = [*message.get("headers", []), *extra]
            await send(message)

        await self.app(scope, limited, with_headers)
