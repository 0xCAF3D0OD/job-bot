"""Protection de l'API (docs/18 §1) : session obligatoire hors Actualités, requêtes venues
d'un autre site refusées.

Middleware ASGI : il lit le cookie, rattache le compte à la requête (`request.state.user`),
renvoie 401 sur une route réservée et prolonge le cookie quand la session l'est.
"""

import json
import re
from http.cookies import SimpleCookie
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from jobbot.auth import service
from jobbot.extension import service as extension_service
from jobbot.log import get_logger

log = get_logger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Ouvert sans connexion : les Actualités du profil principal, en lecture, et la connexion.
PUBLIC_READ = [
    re.compile(r"^/api/news$"),
    re.compile(r"^/api/news/preferences$"),
    re.compile(r"^/api/news/items/\d+/image$"),
    # Documentation interactive (absente en production).
    re.compile(r"^/api/docs"),
    re.compile(r"^/api/openapi\.json$"),
]
PUBLIC_ANY = [re.compile(r"^/api/auth/")]
PROFILE_HEADER = b"x-jobbot-profile"
# Routes de l'extension du navigateur (docs/25) : jeton obligatoire, connexion ou non.
EXTENSION_PREFIX = "/api/extension/"


def is_public(method: str, path: str) -> bool:
    if any(p.match(path) for p in PUBLIC_ANY):
        return True
    return method in SAFE_METHODS and any(p.match(path) for p in PUBLIC_READ)


def _headers(scope: Scope) -> dict[str, str]:
    return {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}


def cookie_token(headers: dict[str, str]) -> str | None:
    raw = headers.get("cookie")
    if not raw:
        return None
    jar: SimpleCookie = SimpleCookie()
    try:
        jar.load(raw)
    except Exception:
        return None
    morsel = jar.get(service.COOKIE)
    return morsel.value if morsel else None


def bearer_token(headers: dict[str, str]) -> str | None:
    value = headers.get("authorization", "")
    return value[7:].strip() or None if value.lower().startswith("bearer ") else None


def cross_site(method: str, headers: dict[str, str]) -> bool:
    """Modification envoyée par la page d'un autre site (protection CSRF)."""
    if method in SAFE_METHODS:
        return False
    fetch_site = headers.get("sec-fetch-site")
    if fetch_site is not None:
        return fetch_site not in ("same-origin", "none")
    origin = headers.get("origin")
    if not origin:
        return False  # client hors navigateur (curl, tests) : pas de risque CSRF
    host = headers.get("x-forwarded-host") or headers.get("host") or ""
    return re.sub(r"^https?://", "", origin).rstrip("/") != host


def secure_cookie(headers: dict[str, str]) -> bool:
    """Cookie réservé au HTTPS, sauf sur la machine elle-même (localhost)."""
    host = (headers.get("x-forwarded-host") or headers.get("host") or "").split(":")[0]
    return host not in ("localhost", "127.0.0.1", "[::1]")


def session_cookie(token: str, headers: dict[str, str], *, clear: bool = False) -> str:
    max_age = 0 if clear else int(service.SESSION_LIFETIME.total_seconds())
    parts = [
        f"{service.COOKIE}={'' if clear else token}",
        "Path=/",
        f"Max-Age={max_age}",
        "HttpOnly",
        "SameSite=Lax",
    ]
    if secure_cookie(headers):
        parts.append("Secure")
    return "; ".join(parts)


async def _json(send: Send, status: int, detail: str) -> None:
    body = json.dumps({"detail": detail}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path: str = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return
        method: str = scope.get("method", "GET")
        headers = _headers(scope)
        if path.startswith(EXTENSION_PREFIX):
            await self._extension(scope, receive, send, headers)
            return
        if cross_site(method, headers):
            log.warning("cross_site_refused", path=path, origin=headers.get("origin"))
            await _json(send, 403, "requête refusée : elle ne vient pas de la plateforme")
            return
        runtime: Any = scope["app"].state.runtime
        state = scope.setdefault("state", {})
        state["user"] = None
        if not runtime.settings.auth_enabled:
            await self.app(scope, receive, send)
            return
        token = cookie_token(headers)
        async with runtime.sessionmaker.begin() as session:
            found = await service.authenticate(session, token)
        state["user"] = found
        if found is None:
            # Sans connexion, le profil d'essai demandé est ignoré : profil principal.
            scope["headers"] = [(k, v) for k, v in scope["headers"] if k != PROFILE_HEADER]
            if not is_public(method, path):
                await _json(send, 401, "connexion requise")
                return
        if not (found and found.renewed and token):
            await self.app(scope, receive, send)
            return
        cookie = session_cookie(token, headers).encode()

        async def send_with_cookie(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((b"set-cookie", cookie))
            await send(message)

        await self.app(scope, receive, send_with_cookie)

    async def _extension(
        self, scope: Scope, receive: Receive, send: Send, headers: dict[str, str]
    ) -> None:
        """Extension : le jeton remplace le cookie. Un jeton n'est jamais joint d'office par
        le navigateur : pas de risque de requête forgée par un autre site."""
        runtime: Any = scope["app"].state.runtime
        async with runtime.sessionmaker.begin() as session:
            found = await extension_service.authenticate(session, bearer_token(headers))
        if found is None:
            await _json(send, 401, "jeton de l'extension absent ou révoqué")
            return
        state = scope.setdefault("state", {})
        state["user"] = None
        state["extension_token"] = found.id
        scope["headers"] = [(k, v) for k, v in scope["headers"] if k != PROFILE_HEADER]
        await self.app(scope, receive, send)
