"""Sessions et limitation des essais de connexion (docs/18 §1).

Le cookie porte un jeton aléatoire ; la base n'en garde que l'empreinte SHA-256. Une session
dure 30 jours et se prolonge à l'usage (au plus une écriture par jour).
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import User, UserSession

COOKIE = "jobbot_session"
SESSION_LIFETIME = timedelta(days=30)
RENEW_AFTER = timedelta(days=1)
FREE_ATTEMPTS = 5
MAX_WAIT_S = 300


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(session: AsyncSession, user_id: int, user_agent: str | None) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    session.add(
        UserSession(
            token_hash=token_hash(token),
            user_id=user_id,
            created_at=now,
            last_seen_at=now,
            expires_at=now + SESSION_LIFETIME,
            user_agent=(user_agent or "")[:200] or None,
        )
    )
    return token


@dataclass(frozen=True)
class Authenticated:
    user_id: int
    username: str
    # Session prolongée : le cookie doit être renvoyé avec sa nouvelle durée.
    renewed: bool


async def authenticate(session: AsyncSession, token: str | None) -> Authenticated | None:
    if not token:
        return None
    now = datetime.now(UTC)
    row = (
        await session.execute(
            select(UserSession, User.username)
            .join(User, User.id == UserSession.user_id)
            .where(UserSession.token_hash == token_hash(token))
        )
    ).first()
    if row is None:
        return None
    stored, username = row
    if stored.expires_at <= now:
        await session.delete(stored)
        return None
    renewed = now - stored.last_seen_at >= RENEW_AFTER
    if renewed:
        stored.last_seen_at = now
        stored.expires_at = now + SESSION_LIFETIME
    return Authenticated(stored.user_id, username, renewed)


async def end_session(session: AsyncSession, token: str | None) -> None:
    if token:
        await session.execute(
            delete(UserSession).where(UserSession.token_hash == token_hash(token))
        )


async def end_all_sessions(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(delete(UserSession).where(UserSession.user_id == user_id))
    return int(getattr(result, "rowcount", 0) or 0)


@dataclass
class Throttle:
    """Après 5 essais ratés (par adresse et par identifiant), attente croissante : 1 s, 2 s,
    4 s… jusqu'à 5 minutes. En mémoire : remis à zéro au redémarrage de l'API."""

    failures: dict[str, tuple[int, float]] = field(default_factory=dict)

    def wait(self, *keys: str) -> int:
        now = time.monotonic()
        waits = [0]
        for key in keys:
            count, last = self.failures.get(key, (0, 0.0))
            if count >= FREE_ATTEMPTS:
                delay = min(2 ** (count - FREE_ATTEMPTS), MAX_WAIT_S)
                waits.append(int(last + delay - now) + 1 if last + delay > now else 0)
        return max(waits)

    def fail(self, *keys: str) -> None:
        now = time.monotonic()
        for key in keys:
            count, _ = self.failures.get(key, (0, 0.0))
            self.failures[key] = (count + 1, now)

    def reset(self, *keys: str) -> None:
        for key in keys:
            self.failures.pop(key, None)
