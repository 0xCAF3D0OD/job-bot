"""Relancer une candidature (docs/38).

L'IA (Claude Haiku) rédige un court message de relance ; elle reçoit le poste, l'entreprise,
la date d'envoi, le résumé de l'offre et les blocs de profil, jamais les coordonnées ni le nom.
La plateforme ajoute l'objet et la signature. Sans IA, un modèle simple est proposé.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from importlib import resources
from typing import Literal

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Application, ApplicationStatus, Draft, Evaluation, Offer
from jobbot.letters.document import format_date
from jobbot.letters.service import load_identity
from jobbot.llm.client import Refused
from jobbot.news.language import detect
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, active_profile, budget_state, record_call

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 400
ESTIMATE_USD = Decimal("0.002")
DESCRIPTION_LIMIT = 2_000
# Relance proposée 10 jours après l'envoi ; « Sans réponse » 14 jours après la relance.
FOLLOW_UP_AFTER = timedelta(days=10)
NO_ANSWER_AFTER = timedelta(days=14)
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/relance-v1.md").read_text("utf-8")
Language = Literal["fr", "de", "en"]
LANGUAGES: dict[Language, str] = {"fr": "français", "de": "allemand", "en": "anglais"}
SUBJECTS = {
    "fr": "Relance \u2013 candidature {title}",
    "de": "Nachfrage \u2013 Bewerbung {title}",
    "en": "Follow-up \u2013 application for {title}",
}
TEMPLATES = {
    "fr": (
        "Madame, Monsieur,\n\nLe {sent}, je vous ai adressé ma candidature pour le poste de "
        "{title}. Ce poste m'intéresse toujours vivement et je reste à votre disposition.\n\n"
        "Pourriez-vous me dire où en est le processus de recrutement, et s'il manque un "
        "élément à mon dossier ?"
    ),
    "de": (
        "Sehr geehrte Damen und Herren,\n\nam {sent} habe ich mich auf die Stelle als {title} "
        "beworben. Die Stelle interessiert mich weiterhin sehr.\n\nKönnten Sie mir mitteilen, "
        "wie der Stand des Auswahlverfahrens ist und ob Ihnen noch Unterlagen fehlen?"
    ),
    "en": (
        "Dear Hiring Team,\n\nOn {sent}, I applied for the {title} position. I remain very "
        "interested in the role.\n\nCould you let me know where the recruitment process "
        "stands, and whether anything is missing from my application?"
    ),
}


@dataclass(frozen=True)
class FollowUpDraft:
    subject: str
    text: str
    language: Language
    # Faux : modèle simple, sans IA (non configurée, plafond atteint ou réponse refusée).
    ai: bool
    reason: str | None = None


def local_today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


def _known(value: str | None) -> Language | None:
    for language in LANGUAGES:
        if value == language:
            return language
    return None


async def _language(
    session: AsyncSession, application: Application, offer: Offer | None
) -> Language:
    """Celle de la lettre envoyée, sinon celle de l'annonce, sinon le français."""
    if application.letter_draft_id:
        letter = await session.get(Draft, application.letter_draft_id)
        if letter is not None and (known := _known(letter.language)):
            return known
    if offer is not None:
        text = " ".join(filter(None, [offer.title, offer.description or offer.snippet]))
        if known := _known(detect(text)):
            return known
    return "fr"


def _sign(text: str, name: str | None) -> str:
    return f"{text.rstrip()}\n\n{name or '[ton prénom et nom]'}"


async def draft(runtime: Runtime, application_id: int) -> FollowUpDraft | None:
    settings = runtime.settings
    async with runtime.sessionmaker() as session:
        application = await session.get(Application, application_id)
        if application is None:
            return None
        offer = await session.get(Offer, application.offer_id) if application.offer_id else None
        evaluation = (
            await session.scalar(select(Evaluation).where(Evaluation.offer_id == offer.id))
            if offer is not None
            else None
        )
        language = await _language(session, application, offer)
        identity = await load_identity(session)
        chunks = await active_profile(session)
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    title = application.job_title
    subject = SUBJECTS[language].format(title=title)
    sent = format_date(application.sent_at, language)

    def template(reason: str) -> FollowUpDraft:
        text = TEMPLATES[language].format(sent=sent, title=title)
        return FollowUpDraft(subject, _sign(text, identity.name), language, ai=False, reason=reason)

    if not settings.llm_configured:
        return template("IA non configurée")
    if spend + ESTIMATE_USD * rate > budget:
        return template("plafond mensuel de l'IA atteint")
    strengths = evaluation.strengths if evaluation is not None else []
    strength = next(
        (s.get("text") for s in strengths if isinstance(s, dict) and s.get("text")), None
    )
    description = ((offer.description or offer.snippet or "") if offer else "")[:DESCRIPTION_LIMIT]
    profile = "\n\n".join(f"[{c.kind}] {c.title}\n{c.content}" for c in chunks)
    content = (
        f"<langue>{LANGUAGES[language]}</langue>\n"
        f"<candidature>{title} — {application.company}, envoyée le {sent}</candidature>\n"
        f"<offre>\n{description}\n</offre>\n"
        f"<point_fort>{strength or ''}</point_fort>\n"
        f"<profil>\n{profile}\n</profil>"
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
        return template("réponse refusée par l'IA")
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            return template(problem)
        raise
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=application.offer_id, rate=rate, purpose="relance")
    text = raw.text.strip().strip('"«» ').strip()
    if not text:
        return template("réponse vide")
    return FollowUpDraft(subject, _sign(text, identity.name), language, ai=True)


async def mark_followed_up(session: AsyncSession, application: Application) -> None:
    """Statut « Relancée », avec la date de la relance."""
    today = local_today()
    application.status = ApplicationStatus.RELANCEE
    application.status_at = today
    application.followed_up_at = today
