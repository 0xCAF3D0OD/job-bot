"""La plateforme en maintenance (docs/79) : pendant une mise à jour, l'API répond « en
maintenance » plutôt que de se tromper à moitié, et l'interface montre sa page d'attente.

Deux cas :

- **la base n'est pas encore à jour** (le code est nouveau, `jobbot migrate` pas encore
  lancé) : toutes les routes de l'API répondent 503, pour tout le monde ;
- **une maintenance annoncée** (`jobbot maintenance on`) : 503 pour tous, sauf l'exploitant,
  qui peut vérifier la plateforme avant de la rouvrir (`jobbot maintenance off`).

Une base injoignable n'est pas une maintenance : les routes le disent elles-mêmes, et l'état
de la plateforme l'explique. L'état est relu au plus toutes les quelques secondes.
"""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.types import ASGIApp, Receive, Scope, Send

from jobbot import accounts, platform
from jobbot.health import check_database
from jobbot.runtime import Runtime

KEY = "maintenance"
# Relu au plus toutes les 5 secondes : « maintenance off » vaut dans les 5 secondes.
CACHE_S = 5.0
MESSAGE = "jobA1 se met à jour, ça revient dans un instant."
# Toujours joignables : l'état de la maintenance (l'interface le sonde), et la connexion (pour
# que l'exploitant entre pendant une maintenance annoncée).
OPEN_PATHS = ("/api/maintenance", "/api/auth/")

Reason = Literal["announced", "update"]


@dataclass(frozen=True)
class State:
    reason: Reason | None = None
    message: str | None = None

    @property
    def active(self) -> bool:
        return self.reason is not None


async def announce(session: AsyncSession, message: str | None) -> None:
    await platform.put(
        session,
        KEY,
        {"message": (message or "").strip()[:300] or None, "since": datetime.now(UTC).isoformat()},
    )


async def lift(session: AsyncSession) -> None:
    await platform.put(session, KEY, None)


async def announced(session: AsyncSession) -> dict[str, Any] | None:
    value = await platform.get(session, KEY)
    return value if isinstance(value, dict) else None


class Watch:
    """L'état de maintenance d'une API, relu au plus toutes les `CACHE_S` secondes."""

    def __init__(self) -> None:
        self._at = float("-inf")
        self._state = State()
        self._owner: int | None = None

    async def state(self, runtime: Runtime) -> tuple[State, int | None]:
        if time.monotonic() - self._at < CACHE_S:
            return self._state, self._owner
        check = await check_database(runtime.engine)
        state, owner = State(), None
        if check.ok and not check.up_to_date:
            state = State("update")
        elif check.ok:
            try:
                async with runtime.sessionmaker() as session:
                    found = await announced(session)
                    if found is not None:
                        state = State("announced", found.get("message"))
                        owner = await accounts.owner_id(session)
            except Exception:  # une lecture ratée ne ferme pas la plateforme
                state = State()
        self._at, self._state, self._owner = time.monotonic(), state, owner
        return state, owner


async def _refuse(send: Send, state: State) -> None:
    body = {
        "detail": MESSAGE,
        "maintenance": True,
        "reason": state.reason,
        "message": state.message,
    }
    await send(
        {
            "type": "http.response.start",
            "status": 503,
            "headers": [
                (b"content-type", b"application/json"),
                (b"cache-control", b"no-store"),
                (b"retry-after", b"10"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": json.dumps(body).encode()})


class MaintenanceMiddleware:
    """Placé à l'intérieur de la connexion : il sait si la requête vient de l'exploitant."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path: str = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith("/api/") or path.startswith(OPEN_PATHS):
            await self.app(scope, receive, send)
            return
        app_state = scope["app"].state
        state, owner = await app_state.maintenance.state(app_state.runtime)
        bypass = state.reason == "announced" and owner is not None and accounts.current() == owner
        if state.active and not bypass:
            await _refuse(send, state)
            return
        await self.app(scope, receive, send)
