"""Invitations et réinitialisations (docs/65 §2) : des liens à usage unique.

Seul l'exploitant les crée et les transmet lui-même (la plateforme n'envoie pas d'e-mail).
Le lien porte un jeton aléatoire ; la base n'en garde que l'empreinte SHA-256. Une
invitation vaut 7 jours, une réinitialisation 24 heures ; une nouvelle réinitialisation
remplace la précédente.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.auth import passwords
from jobbot.auth.service import end_all_sessions, token_hash
from jobbot.db.models import AccountLink, User

Kind = Literal["invite", "reset"]
LIFETIME: dict[str, timedelta] = {"invite": timedelta(days=7), "reset": timedelta(hours=24)}
PREFIX = "jba_"
USERNAME_MAX = 40


class LinkError(Exception):
    """Lien inconnu, déjà utilisé ou expiré, ou saisie refusée ; le message est pour l'écran."""

    def __init__(self, message: str, reason: Literal["unknown", "gone", "invalid"]) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Created:
    link: AccountLink
    token: str


async def create(session: AsyncSession, kind: Kind, user_id: int | None = None) -> Created:
    now = datetime.now(UTC)
    if kind == "reset":
        await session.execute(
            delete(AccountLink).where(
                AccountLink.kind == "reset",
                AccountLink.user_id == user_id,
                AccountLink.used_at.is_(None),
            )
        )
    token = PREFIX + secrets.token_urlsafe(32)
    link = AccountLink(
        kind=kind,
        user_id=user_id,
        token_hash=token_hash(token),
        created_at=now,
        expires_at=now + LIFETIME[kind],
    )
    session.add(link)
    await session.flush()
    return Created(link, token)


async def find(session: AsyncSession, token: str) -> tuple[AccountLink, User | None]:
    """Le lien encore valable ; sinon LinkError (gone : utilisé ou expiré)."""
    link = await session.scalar(
        select(AccountLink).where(AccountLink.token_hash == token_hash(token))
    )
    if link is None or not token.startswith(PREFIX):
        raise LinkError("lien inconnu : demande-en un nouveau", "unknown")
    if link.used_at is not None:
        raise LinkError("ce lien a déjà servi : demande-en un nouveau", "gone")
    if link.expires_at <= datetime.now(UTC):
        raise LinkError("ce lien a expiré : demande-en un nouveau", "gone")
    user = await session.get(User, link.user_id) if link.user_id is not None else None
    return link, user


async def use(session: AsyncSession, token: str, username: str | None, password: str) -> User:
    """Crée le compte (invitation) ou change le mot de passe (réinitialisation) ; le lien ne
    sert plus. Les sessions ouvertes du compte sont fermées après une réinitialisation."""
    link, user = await find(session, token)
    if problem := passwords.check_strength(password):
        raise LinkError(f"mot de passe refusé : {problem}", "invalid")
    now = datetime.now(UTC)
    if link.kind == "invite":
        name = (username or "").strip()
        if not name or len(name) > USERNAME_MAX:
            raise LinkError(f"identifiant requis, {USERNAME_MAX} caractères au plus", "invalid")
        taken = await session.scalar(
            select(func.count()).select_from(User).where(func.lower(User.username) == name.lower())
        )
        if taken:
            raise LinkError("cet identifiant est déjà pris : choisis-en un autre", "invalid")
        user = User(username=name, password_hash=passwords.hash_password(password))
        session.add(user)
        await session.flush()
    else:
        assert user is not None
        user.password_hash = passwords.hash_password(password)
        user.password_changed_at = now
        await end_all_sessions(session, user.id)
    link.used_at = now
    return user
