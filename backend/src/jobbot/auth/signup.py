"""S'inscrire, sur demande (docs/102).

N'importe qui demande un compte depuis la page de connexion ; le compte attend que
l'exploitant l'accepte (`users.approved_at` vide). Tant qu'il attend : ni connexion, ni
session, ni tâche, ni profil, ni adresse de réception. Refuser efface le compte ; une demande
sans réponse est effacée après 30 jours.

Tout se fait au nom de l'exploitant, comme une invitation : lui seul voit et crée les comptes.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, null, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts, platform
from jobbot.auth import passwords
from jobbot.auth.links import LinkError, free_username
from jobbot.db.models import User
from jobbot.runtime import Runtime

OPEN_KEY = "signup_open"
MAX_PENDING = 20
NOTE_MAX = 300
KEEP_PENDING = timedelta(days=30)
CLOSED = "les demandes de compte sont fermées pour le moment"


async def switched_on(session: AsyncSession) -> bool:
    """L'interrupteur de l'exploitant, « Accepter des demandes de compte » (activé d'office)."""
    return bool(await platform.get(session, OPEN_KEY, True))


async def pending_count(session: AsyncSession) -> int:
    return int(
        await session.scalar(
            select(func.count()).select_from(User).where(User.approved_at.is_(None))
        )
        or 0
    )


async def is_open(runtime: Runtime) -> bool:
    """Ouvertes : connexion activée, hors démo, exploitant configuré, interrupteur allumé,
    moins de 20 demandes en attente."""
    settings = runtime.settings
    if settings.demo or not settings.auth_enabled:
        return False
    async with runtime.sessionmaker.begin() as session:
        if not await accounts.has_password(session):
            return False
        owner = await accounts.owner_id(session)
    with accounts.use(owner):
        async with runtime.sessionmaker() as session:
            return await switched_on(session) and await pending_count(session) < MAX_PENDING


async def request(session: AsyncSession, username: str, password: str, note: str | None) -> User:
    """Le compte en attente, sans profil ni adresse ; sinon LinkError (saisie refusée)."""
    if problem := passwords.check_strength(password):
        raise LinkError(f"mot de passe refusé : {problem}", "invalid")
    name = await free_username(session, username)
    user = User(
        username=name,
        password_hash=passwords.hash_password(password),
        # Explicitement vide : sinon la base accepterait le compte d'office (valeur par défaut).
        approved_at=null(),
        signup_note=(note or "").strip()[:NOTE_MAX] or None,
    )
    session.add(user)
    await session.flush()
    return user


async def approve(session: AsyncSession, account_id: int) -> bool:
    """Accepte la demande : le compte devient actif (plafond de l'IA par défaut)."""
    user = await session.get(User, account_id)
    if user is None or user.approved_at is not None:
        return False
    user.approved_at = datetime.now(UTC)
    user.signup_note = None
    return True


async def purge(runtime: Runtime) -> int:
    """Les demandes sans réponse depuis 30 jours (tâche `reminders`, au tour de l'exploitant :
    lui seul voit les comptes)."""
    async with runtime.sessionmaker.begin() as session:
        if not await accounts.is_owner(session):
            return 0
        result = await session.execute(
            delete(User).where(
                User.approved_at.is_(None),
                User.created_at < datetime.now(UTC) - KEEP_PENDING,
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)
