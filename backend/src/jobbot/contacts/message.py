"""Premier message à un contact (docs/31 §3), rédigé par l'IA.

L'IA reçoit le poste, l'entreprise, le rôle du destinataire et les blocs de profil ; jamais
de nom (ni le sien, ni le tien) : le texte porte « [Prénom] » et « [ton prénom] ».
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources

import anthropic

from jobbot.db.models import Application, Offer
from jobbot.llm.client import Refused
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, active_profile, budget_state, record_call

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 400
ESTIMATE_USD = Decimal("0.002")
DESCRIPTION_LIMIT = 3_000
# Limite d'une invitation LinkedIn avec note.
INVITE_LIMIT = 300
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/contact-v1.md").read_text("utf-8")
ROLES = {
    "recruiter": "personne du recrutement (RH, talent acquisition)",
    "manager": "futur responsable du poste",
    "team": "membre de l'équipe du poste",
    "alumni": "ancien de la même école que l'expéditeur",
    "other": "personne de l'entreprise",
}
CHANNELS = {
    "linkedin_invite": "invitation LinkedIn (300 caractères au plus)",
    "linkedin_message": "message LinkedIn (120 mots au plus)",
    "email": "e-mail (120 mots au plus)",
}


class MessageUnavailable(Exception):
    """IA non configurée, plafond atteint, poste introuvable ou réponse refusée."""


@dataclass(frozen=True)
class Draft:
    text: str
    limit: int | None


async def draft(
    runtime: Runtime,
    *,
    offer_id: int | None,
    application_id: int | None,
    role: str,
    channel: str,
) -> Draft:
    settings = runtime.settings
    if not settings.llm_configured:
        raise MessageUnavailable("IA non configurée")
    async with runtime.sessionmaker() as session:
        application = await session.get(Application, application_id) if application_id else None
        offer_id = offer_id or (application.offer_id if application else None)
        offer = await session.get(Offer, offer_id) if offer_id else None
        if offer is None and application is None:
            raise MessageUnavailable("poste introuvable")
        chunks = await active_profile(session)
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        raise MessageUnavailable("plafond mensuel de l'IA atteint")
    if offer is not None:
        title, company = offer.title, offer.company
        description = (offer.description or offer.snippet or "")[:DESCRIPTION_LIMIT]
    else:
        assert application is not None
        title, company, description = application.job_title, application.company, ""
    profile = "\n\n".join(f"[{c.kind}] {c.title}\n{c.content}" for c in chunks)
    content = (
        f"<offre>\n{title} — {company or 'entreprise non indiquée'}\n{description}\n</offre>\n"
        f"<profil>\n{profile}\n</profil>\n"
        f"<destinataire>{ROLES.get(role, ROLES['other'])}</destinataire>\n"
        f"<canal>{CHANNELS.get(channel, CHANNELS['linkedin_message'])}</canal>"
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
        raise MessageUnavailable("message refusé par l'IA") from None
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise MessageUnavailable(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=offer_id, rate=rate, purpose="contact")
    text = raw.text.strip().strip('"«» ').strip()
    if not text:
        raise MessageUnavailable("réponse vide, réessaie")
    return Draft(text, INVITE_LIMIT if channel == "linkedin_invite" else None)
