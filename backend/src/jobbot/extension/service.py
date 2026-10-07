"""Extension du navigateur (docs/25) : jetons, candidature reconnue, réponses aux questions.

L'extension remplit le formulaire de l'employeur sans jamais l'envoyer. Elle se relie à la
plateforme par un jeton révocable ; seule son empreinte est gardée en base.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from urllib.parse import urlsplit

import anthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.auth.service import token_hash
from jobbot.db.models import Draft, DraftKind, ExtensionToken, Offer, OfferLink, OfferStatus
from jobbot.letters.service import current_draft
from jobbot.llm.client import Refused
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, active_profile, budget_state, record_call

PREFIX = "jbx_"
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 600
ESTIMATE_USD = Decimal("0.01")
DESCRIPTION_LIMIT = 4_000
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/form-answer-v1.md").read_text("utf-8")
)
# Offres proposées quand la page n'est pas reconnue : celles en cours de préparation.
CHOICES = 10


# --- Jetons -------------------------------------------------------------------------------


async def create_token(session: AsyncSession, name: str) -> tuple[ExtensionToken, str]:
    token = PREFIX + secrets.token_urlsafe(32)
    row = ExtensionToken(name=name, token_hash=token_hash(token))
    session.add(row)
    await session.flush()
    return row, token


async def authenticate(session: AsyncSession, token: str | None) -> ExtensionToken | None:
    if not token or not token.startswith(PREFIX):
        return None
    row = await session.scalar(
        select(ExtensionToken).where(
            ExtensionToken.token_hash == token_hash(token), ExtensionToken.revoked_at.is_(None)
        )
    )
    if row is not None:
        row.last_used_at = datetime.now(UTC)
    return row


# --- Candidature reconnue -----------------------------------------------------------------


def _key(url: str | None) -> tuple[str, str] | None:
    """Hôte (sans www) et chemin (sans / final), pour comparer deux adresses."""
    if not url:
        return None
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    host = parts.hostname.lower().removeprefix("www.")
    return host, parts.path.rstrip("/").lower()


def same_page(page: str, known: str | None) -> bool:
    """La page du formulaire correspond-elle à l'annonce connue ? Même site, et l'un des
    chemins prolonge l'autre (…/jobs/123 et …/jobs/123/apply)."""
    a, b = _key(page), _key(known)
    if a is None or b is None or a[0] != b[0] or len(b[1]) <= 1 or len(a[1]) <= 1:
        return False
    return a[1] == b[1] or a[1].startswith(b[1] + "/") or b[1].startswith(a[1] + "/")


async def match(session: AsyncSession, url: str) -> tuple[Offer | None, list[Offer]]:
    """L'offre de cette page (si reconnue) et les offres en préparation, à choisir sinon."""
    found: Offer | None = None
    page = _key(url)
    if page is not None:
        candidates = await session.scalars(
            select(Offer).where(
                Offer.status.not_in((OfferStatus.IGNORED,)),
                (Offer.employer_url.ilike(f"%{page[0]}%"))
                | (Offer.apply_url.ilike(f"%{page[0]}%")),
            )
        )
        for offer in candidates:
            if same_page(url, offer.employer_url) or same_page(url, offer.apply_url):
                found = offer
                break
        if found is None:
            rows = await session.execute(
                select(Offer, OfferLink.url)
                .join(OfferLink, OfferLink.offer_id == Offer.id)
                .where(OfferLink.url.ilike(f"%{page[0]}%"))
            )
            found = next((o for o, link in rows if same_page(url, link)), None)
    # Offres en préparation, la dernière rédigée d'abord.
    last_draft = (
        select(Draft.offer_id, func.max(Draft.created_at).label("created_at"))
        .group_by(Draft.offer_id)
        .subquery()
    )
    choices = list(
        await session.scalars(
            select(Offer)
            .outerjoin(last_draft, last_draft.c.offer_id == Offer.id)
            .where(Offer.status == OfferStatus.PREPARING)
            .order_by(last_draft.c.created_at.desc().nulls_last(), Offer.id.desc())
            .limit(CHOICES)
        )
    )
    return found, choices


# --- Réponse de l'IA à une question libre -------------------------------------------------


class AnswerUnavailable(Exception):
    """IA non configurée, plafond atteint, offre introuvable ou réponse refusée."""


@dataclass(frozen=True)
class Answer:
    text: str


async def answer(runtime: Runtime, offer_id: int, question: str) -> Answer:
    """Proposition de réponse : la question, l'offre, la lettre et les blocs de profil,
    jamais les coordonnées."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise AnswerUnavailable("IA non configurée")
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise AnswerUnavailable("offre introuvable")
        letter = await current_draft(session, offer_id, DraftKind.LETTER)
        chunks = await active_profile(session)
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        raise AnswerUnavailable("plafond mensuel de l'IA atteint")
    paragraphs = (
        [p.get("text", "") for p in (letter.content.get("paragraphs") or [])] if letter else []
    )
    profile = "\n\n".join(f"[{c.kind}] {c.title}\n{c.content}" for c in chunks)
    description = (offer.description or offer.snippet or "")[:DESCRIPTION_LIMIT]
    content = (
        f"<offre>\n{offer.title} — {offer.company or 'entreprise non indiquée'}\n"
        f"{description}\n</offre>\n"
        f"<lettre>\n{chr(10).join(paragraphs)}\n</lettre>\n"
        f"<profil>\n{profile}\n</profil>\n"
        f"<question>\n{question}\n</question>"
    )
    params = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
    }
    try:
        raw = await scoring_service.make_client(settings).score(params)
    except Refused:
        raise AnswerUnavailable("réponse refusée par l'IA") from None
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise AnswerUnavailable(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=offer_id, rate=rate, purpose="form")
    text = raw.text.strip().strip('"«» ').strip()
    if not text:
        raise AnswerUnavailable("réponse vide, réessaie")
    return Answer(text)
