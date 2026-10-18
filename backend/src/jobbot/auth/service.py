"""Sessions et limitation des essais de connexion (docs/18 §1).

Le cookie porte un jeton aléatoire ; la base n'en garde que l'empreinte SHA-256. Une session
dure 30 jours et se prolonge à l'usage (au plus une écriture par jour), jusqu'à 90 jours après
la connexion : il faut alors se reconnecter (docs/78 §2).
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
SESSION_MAX_AGE = timedelta(days=90)
RENEW_AFTER = timedelta(days=1)
FREE_ATTEMPTS = 5
MAX_WAIT_S = 300
FORGET_AFTER_S = 24 * 3600


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
            # Un compte suspendu (docs/65 §2) n'a plus de session valable.
            .where(UserSession.token_hash == token_hash(token), User.suspended_at.is_(None))
        )
    ).first()
    if row is None:
        return None
    stored, username = row
    limit = stored.created_at + SESSION_MAX_AGE
    if stored.expires_at <= now or limit <= now:
        await session.delete(stored)
        return None
    renewed = now - stored.last_seen_at >= RENEW_AFTER and stored.expires_at < limit
    if renewed:
        stored.last_seen_at = now
        stored.expires_at = min(now + SESSION_LIFETIME, limit)
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
    """Après 5 essais ratés (par adresse, et par adresse et identifiant), attente croissante :
    1 s, 2 s, 4 s… jusqu'à 5 minutes. Compter par identifiant seul laisserait un inconnu
    bloquer la connexion de quelqu'un d'autre (docs/78 §2). En mémoire : remis à zéro au
    redémarrage de l'API ; un essai raté est oublié après une journée."""

    failures: dict[str, tuple[int, float]] = field(default_factory=dict)

    def _forget_old(self, now: float) -> None:
        for key in [k for k, (_, last) in self.failures.items() if now - last > FORGET_AFTER_S]:
            del self.failures[key]

    def wait(self, *keys: str) -> int:
        now = time.monotonic()
        self._forget_old(now)
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
