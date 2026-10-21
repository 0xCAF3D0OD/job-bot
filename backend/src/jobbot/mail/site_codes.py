"""Les codes et les messages des sites, côté compte (docs/112).

- Un code reconnu (`mail/codes.py`) est annoncé dans la cloche et sur le téléphone, montré
  en haut de la page Alertes, et lu par l'extension pour le remplir ; il s'efface au bout de
  30 minutes.
- « J'attends un code » : la boîte est relevée toutes les 15 secondes pendant 5 minutes.
- Les autres e-mails des sites (bienvenue, alerte modifiée…) se lisent dans « Messages des
  sites », 30 jours.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bs4 import BeautifulSoup
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import Notification, Search, Setting
from jobbot.log import get_logger
from jobbot.mail.codes import spaced
from jobbot.mail.message import parse_email
from jobbot.notify import service as notify
from jobbot.runtime import Runtime
from jobbot.worker.queue import enqueue

log = get_logger(__name__)

CODE_KIND = "code"
MESSAGE_KIND = "message"
NOTIFICATION_KIND = "site_code"
CODE_SHOWN_FOR = timedelta(minutes=30)
# L'extension ne remplit qu'un code tout frais.
CODE_FILLED_WITHIN = timedelta(minutes=10)
MESSAGES_KEPT_FOR = timedelta(days=30)
FAST_COLLECT_JOB = "collect_fast"
EXPECT_KEY = "code_expected"
# Le relevé rapide : 6 demandes par heure au plus, par compte.
EXPECT_PER_HOUR = 6
MAX_TEXT = 20_000


@dataclass(frozen=True)
class SiteCode:
    search_id: int
    site: str
    code: str
    received_at: datetime


async def announce(runtime: Runtime, site: str, code: str) -> None:
    """Dans la cloche et sur le téléphone : le code lui-même, lisible sans ouvrir jobA1."""
    await notify.deliver(
        runtime,
        notify.Message(
            title=f"Code {site}",
            message=f"{site} : {spaced(code)}",
            priority=4,
            tags=["key"],
        ),
        kind=NOTIFICATION_KIND,
        link="/candidatures/alertes",
    )


async def current(runtime: Runtime, *, within: timedelta = CODE_SHOWN_FOR) -> list[SiteCode]:
    """Les codes encore valables du compte, le plus récent d'abord."""
    since = datetime.now(UTC) - within
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(
            select(Search)
            .where(Search.kind == CODE_KIND, Search.code.is_not(None), Search.received_at >= since)
            .order_by(Search.received_at.desc())
        )
        return [SiteCode(s.id, s.source, s.code or "", s.received_at) for s in rows]


async def latest(runtime: Runtime, site: str) -> SiteCode | None:
    """Le code de ce site reçu il y a moins de 10 minutes (pour l'extension)."""
    found = await current(runtime, within=CODE_FILLED_WITHIN)
    return next((c for c in found if c.site == site), None)


async def expect(runtime: Runtime) -> bool:
    """« J'attends un code » : le relevé rapide, 6 fois par heure au plus. False : trop tôt."""
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        value = await session.scalar(select(Setting.value).where(Setting.key == EXPECT_KEY))
        recent = [
            at
            for at in (value if isinstance(value, list) else [])
            if isinstance(at, str) and now - datetime.fromisoformat(at) < timedelta(hours=1)
        ]
        if len(recent) >= EXPECT_PER_HOUR:
            return False
        statement = insert(Setting).values(key=EXPECT_KEY, value=[*recent, now.isoformat()])
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=["user_id", "key"], set_={"value": statement.excluded.value}
            )
        )
    await enqueue(runtime.settings, FAST_COLLECT_JOB)
    return True


@dataclass(frozen=True)
class SiteMessage:
    id: int
    site: str
    subject: str | None
    received_at: datetime


async def messages(runtime: Runtime) -> list[SiteMessage]:
    since = datetime.now(UTC) - MESSAGES_KEPT_FOR
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(
            select(Search)
            .where(Search.kind == MESSAGE_KIND, Search.received_at >= since)
            .order_by(Search.received_at.desc())
            .limit(50)
        )
        return [SiteMessage(s.id, s.source, s.subject, s.received_at) for s in rows]


async def message_text(runtime: Runtime, search_id: int) -> str | None:
    """Le texte du message, sans images ni pièces jointes. None : pas un message du compte."""
    async with runtime.sessionmaker() as session:
        search = await session.get(Search, search_id)
    if search is None or search.kind != MESSAGE_KIND:
        return None
    try:
        raw = runtime.storage.get(search.raw_key)
    except FileNotFoundError:
        return ""
    email = parse_email(raw, fallback_received=search.received_at)
    text = email.text
    if not text and email.html:
        soup = BeautifulSoup(email.html, "html.parser")
        for tag in soup(["script", "style", "img"]):
            tag.decompose()
        text = soup.get_text("\n")
    lines = [" ".join(line.split()) for line in (text or "").splitlines()]
    return "\n".join(line for line in lines if line)[:MAX_TEXT]


async def purge(runtime: Runtime, now: datetime | None = None) -> int:
    """Les codes effacés au bout de 30 minutes (dans le journal et la cloche), les codes et
    messages supprimés au bout de 30 jours, avec leur e-mail."""
    now = now or datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Search)
            .where(
                Search.kind == CODE_KIND,
                Search.code.is_not(None),
                Search.received_at < now - CODE_SHOWN_FOR,
            )
            .values(code=None)
        )
        await session.execute(
            update(Notification)
            .where(
                Notification.kind == NOTIFICATION_KIND,
                Notification.created_at < now - CODE_SHOWN_FOR,
                Notification.message != "Code expiré",
            )
            .values(message="Code expiré")
        )
        old = list(
            await session.scalars(
                select(Search).where(
                    Search.kind.in_([CODE_KIND, MESSAGE_KIND]),
                    Search.received_at < now - MESSAGES_KEPT_FOR,
                )
            )
        )
        for search in old:
            runtime.storage.delete(search.raw_key)
        if old:
            await session.execute(delete(Search).where(Search.id.in_([s.id for s in old])))
    return len(old)
