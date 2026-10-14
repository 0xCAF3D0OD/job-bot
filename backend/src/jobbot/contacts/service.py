"""Contacts dans l'entreprise (docs/31) : recherches déjà remplies et relance des contacts.

La plateforme ne lit pas LinkedIn et ne contacte personne : elle ouvre des recherches par
mots-clés (les seules qu'une adresse peut pré-remplir sans compte) et garde la trace de tes
prises de contact.
"""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Application, Contact, Offer, ProfileChunk
from jobbot.notify.service import Message, deliver
from jobbot.runtime import Runtime

PEOPLE_SEARCH = "https://www.linkedin.com/search/results/people/?"
FOLLOW_UP_AFTER = timedelta(days=7)
ROLE_WORDS = "recruiter OR talent OR RH OR HR"
# Mots du titre qui ne disent rien du métier (« (H/F) », « Senior », taux…).
_NOISE = re.compile(
    r"\(.*?\)|\d+(\s*-\s*\d+)?\s*%|\b(h/f|f/h|m/w/d|w/m/d|senior|junior|lead|stagiaire|intern)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SearchLink:
    kind: str  # recruiting | team | alumni
    label: str
    url: str


def _people(keywords: str) -> str:
    return PEOPLE_SEARCH + urlencode({"keywords": " ".join(keywords.split())})


def role_words(title: str) -> str:
    """Les deux ou trois mots du poste qui disent le métier : « DevOps Engineer (H/F) 80-100 % »
    devient « DevOps Engineer »."""
    words = [w for w in _NOISE.sub(" ", title).replace("/", " ").split() if len(w) > 1]
    return " ".join(words[:3])


def school_of(title: str) -> str | None:
    """« 42 Lausanne (2021-2023) et maturité professionnelle » → « 42 Lausanne »."""
    head = re.split(r"\(|,| et | and |[\u2013\u2014]| - ", title, maxsplit=1)[0]
    head = " ".join(head.split())
    return head if len(head) >= 2 else None


async def schools(session: AsyncSession) -> list[str]:
    found: list[str] = []
    for title in await session.scalars(
        select(ProfileChunk.title)
        .where(ProfileChunk.kind == "formation", ProfileChunk.active.is_(True))
        .order_by(ProfileChunk.id)
    ):
        school = school_of(title)
        if school and school not in found:
            found.append(school)
    return found[:2]


def search_links(company: str, title: str, school_names: list[str]) -> list[SearchLink]:
    links = [
        SearchLink("recruiting", "Recrutement", _people(f"{company} {ROLE_WORDS}")),
    ]
    role = role_words(title)
    if role:
        links.append(
            SearchLink("team", f"L'équipe du poste ({role})", _people(f"{company} {role}"))
        )
    for school in school_names:
        links.append(SearchLink("alumni", f"Anciens de {school}", _people(f"{company} {school}")))
    return links


def _today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


async def due(session: AsyncSession, today: date | None = None) -> list[Contact]:
    """Prises de contact restées sans réponse depuis 7 jours, pas encore rappelées."""
    limit = (today or _today()) - FOLLOW_UP_AFTER
    return list(
        await session.scalars(
            select(Contact).where(
                Contact.answered_on.is_(None),
                Contact.reminded_at.is_(None),
                Contact.contacted_on <= limit,
            )
        )
    )


async def _company(session: AsyncSession, contact: Contact) -> str:
    if contact.offer_id and (offer := await session.get(Offer, contact.offer_id)):
        return offer.company or offer.title
    if contact.application_id and (app := await session.get(Application, contact.application_id)):
        return app.company
    return "l'entreprise"


async def notify_contacts(runtime: Runtime) -> int:
    """Une alerte par prise de contact sans réponse depuis 7 jours, une seule fois."""
    async with runtime.sessionmaker() as session:
        contacts = await due(session)
        labels = [(c.id, c.name, await _company(session, c), c.offer_id) for c in contacts]
    for contact_id, name, company, offer_id in labels:
        who = name or "ton contact"
        link = f"/candidatures/offres?offre={offer_id}" if offer_id else "/candidatures/suivi"
        await deliver(
            runtime,
            Message(
                title=f"Relancer {who} chez {company} ?",
                message=(
                    "Pas de réponse depuis une semaine : un court message de relance, "
                    "ou passe à autre chose."
                ),
                tags=["speech_balloon"],
            ),
            kind="contact_follow_up",
            link=link,
        )
        async with runtime.sessionmaker.begin() as session:
            found = await session.get(Contact, contact_id)
            if found is not None:
                found.reminded_at = datetime.now(UTC)
    return len(labels)
