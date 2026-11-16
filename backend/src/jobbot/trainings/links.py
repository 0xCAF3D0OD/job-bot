"""Vérification des liens du catalogue des formations (Kevin, 16.11.2026).

Un lien mort (404, 410, ou page « 404 / page non trouvée » après redirection) retire la fiche.
Une panne passagère (erreur 5xx, délai dépassé, connexion refusée, page « Cookie not accepted »)
n'est pas un lien mort : la fiche passe « à revérifier » et la tâche réessaie 24 h plus tard.
Un lien vérifié est revu tous les 30 jours. Rien de personnel n'est envoyé : seule l'adresse
publique de la formation est demandée.
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Training
from jobbot.log import get_logger

log = get_logger(__name__)

LinkStatus = Literal["ok", "a_reverifier", "mort"]
RECHECK_AFTER = timedelta(hours=24)
OK_AFTER = timedelta(days=30)
TIMEOUT = 20.0
# Assez pour reconnaître une page d'erreur, sans tout lire.
READ_LIMIT = 64_000
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; jobA1-verification-liens)"}
_COOKIE_WALL = re.compile(r"cookie\s+not\s+accepted", re.I)
_SOFT_404 = re.compile(
    r"<title>[^<]*(\b404\b|page non trouv|page introuvable|not found)[^<]*</title>", re.I
)


def classify(status_code: int, content_type: str, body: str) -> LinkStatus:
    """Règle du vérificateur, sans réseau : testée à part."""
    if status_code in (404, 410):
        return "mort"
    if status_code >= 500 or status_code in (403, 408, 429):
        return "a_reverifier"
    if status_code >= 400:
        return "mort"
    if "html" in content_type:
        if _COOKIE_WALL.search(body):
            return "a_reverifier"
        if _SOFT_404.search(body):
            return "mort"
    return "ok"


async def check(client: httpx.AsyncClient, url: str) -> LinkStatus:
    try:
        async with client.stream("GET", url) as response:
            body = b""
            content_type = response.headers.get("content-type", "")
            if "html" in content_type:
                async for chunk in response.aiter_bytes():
                    body += chunk
                    if len(body) >= READ_LIMIT:
                        break
            return classify(response.status_code, content_type, body.decode("utf-8", "replace"))
    except httpx.HTTPError as exc:
        log.info("training_link_unreachable", url=url, error=type(exc).__name__)
        return "a_reverifier"


def next_check(status: LinkStatus, now: datetime) -> datetime | None:
    if status == "mort":
        return None
    return now + (OK_AFTER if status == "ok" else RECHECK_AFTER)


async def check_due(session: AsyncSession, client: httpx.AsyncClient) -> int:
    """Vérifie les fiches du catalogue dont la date est passée ; renvoie le nombre vérifié."""
    now = datetime.now(UTC)
    due = (
        await session.scalars(
            select(Training).where(
                Training.profile_id.is_(None),
                Training.link_status != "mort",
                or_(Training.link_next_check.is_(None), Training.link_next_check <= now),
            )
        )
    ).all()
    for training in due:
        status = await check(client, training.url)
        if status != training.link_status:
            log.info("training_link_status", training=training.id, status=status)
        training.link_status = status
        training.link_next_check = next_check(status, now)
    return len(due)
