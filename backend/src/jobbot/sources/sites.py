"""Sites suivis (docs/11 §2) : reconnaître le site d'une alerte et la lire par l'IA au besoin."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import ParseStatus, Site
from jobbot.letters.service import load_identity
from jobbot.llm import alert as alert_llm
from jobbot.llm.client import Refused
from jobbot.llm.scoring import InvalidScore
from jobbot.log import get_logger
from jobbot.mail.message import ParsedEmail
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call
from jobbot.sources.base import ParsedAlert

log = get_logger(__name__)
# Estimation prudente d'une lecture (e-mail long), pour le plafond mensuel.
ALERT_ESTIMATE_USD = Decimal("0.03")


@dataclass(frozen=True)
class SiteData:
    slug: str
    name: str
    senders: tuple[str, ...]
    reader: str
    active: bool


async def load_sites(session: AsyncSession) -> list[SiteData]:
    return [
        SiteData(s.slug, s.name, tuple(x.lower() for x in s.senders), s.reader, s.active)
        for s in await session.scalars(select(Site).order_by(Site.id))
    ]


def match_site(sites: list[SiteData], email: ParsedEmail) -> SiteData | None:
    """Le site dont un expéditeur correspond : adresse exacte, ou domaine (et sous-domaines)."""
    domain = email.sender_domain
    for site in sites:
        for sender in site.senders:
            if "@" in sender:
                if email.sender == sender:
                    return site
            elif domain == sender or domain.endswith("." + sender):
                return site
    return None


@dataclass(frozen=True)
class AiReading:
    status: ParseStatus
    alert: ParsedAlert
    error: str | None


async def read_with_ai(runtime: Runtime, email: ParsedEmail, site: SiteData) -> AiReading:
    """Lit l'alerte par l'IA ; sans clé ou au plafond, elle reste « non reconnue » et sera
    relue plus tard (Réglages, « Relire les alertes non reconnues »)."""
    empty = ParsedAlert(None, [])
    settings = runtime.settings
    if not settings.llm_configured:
        return AiReading(ParseStatus.UNRECOGNIZED, empty, "IA non configurée : alerte gardée")
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
        identity = await load_identity(session)
    if spend + ALERT_ESTIMATE_USD * rate > budget:
        return AiReading(ParseStatus.UNRECOGNIZED, empty, "plafond de l'IA atteint : alerte gardée")
    prepared = alert_llm.prepare(email, [identity.name or ""])
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(alert_llm.request_params(prepared, email.subject))
    except Refused:
        return AiReading(ParseStatus.FAILED, empty, "lecture refusée par l'IA")
    except anthropic.APIStatusError as exc:
        problem = account_problem(exc)
        return AiReading(ParseStatus.UNRECOGNIZED, empty, problem or f"API ({exc.status_code})")
    except anthropic.APIConnectionError:
        return AiReading(ParseStatus.UNRECOGNIZED, empty, "IA injoignable : alerte gardée")
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="alert")
    try:
        alert = alert_llm.parse_output(raw.text, prepared, email.subject)
    except InvalidScore as exc:
        return AiReading(ParseStatus.FAILED, empty, str(exc))
    log.info("alert_read_by_ai", site=site.slug, offers=len(alert.offers))
    status = ParseStatus.PARSED if alert.offers else ParseStatus.EMPTY
    return AiReading(status, alert, None)
