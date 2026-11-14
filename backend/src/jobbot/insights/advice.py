"""« Ce que jobA1 conseille » (Bilan, Résultats, planche BilanOrdinateur ; Kevin, 2026-11-14).

De simples comptes sur tes données, sans IA ni migration. Deux types de conseil, avec leur base :

- une façon de postuler, ou un site, qui ne donne aucune réponse alors que d'autres en donnent :
  au moins `MIN_BASE` candidatures concernées, envoyées depuis au moins `SETTLED_DAYS` jours ;
- une compétence demandée et absente de ton profil : au moins `MIN_BASE` offres retenues qui la
  demandent.

En dessous du seuil, pas de conseil ; sans conseil, le bloc est caché.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Evaluation, Offer

if TYPE_CHECKING:
    from jobbot.insights.service import Facts

MIN_BASE = 5
# Une candidature plus récente peut encore recevoir sa réponse : elle ne compte pas encore.
SETTLED_DAYS = 14
SKILL_MAX = 40

# La façon de postuler, lue sur la candidature : « électronique » avec un lien vers le formulaire
# est un formulaire en ligne ; sans lien mais avec une adresse e-mail, un e-mail direct.
CHANNELS: dict[str, tuple[str, str]] = {
    "form": (
        "Les formulaires en ligne ne répondent pas",
        "Essaie l'e-mail direct au service RH quand l'annonce en donne un.",
    ),
    "email": (
        "Les e-mails directs ne reçoivent pas de réponse",
        "Essaie le formulaire en ligne de l'annonce quand il y en a un.",
    ),
    "letter": (
        "Les lettres par la poste ne reçoivent pas de réponse",
        "Essaie le formulaire en ligne ou l'e-mail quand l'annonce en donne un.",
    ),
}
SITE_TEXT = "Tes réponses viennent d'ailleurs : garde plus de temps pour les autres sites."
SKILL_TEXT = "La formation peut être financée par l'ORP."


@dataclass
class Advice:
    kind: Literal["channel", "site", "skill"]
    title: str
    text: str
    # La base du conseil : « d'après 8 candidatures », « d'après 22 offres ».
    base: int
    base_unit: Literal["applications", "offers"]
    # Le conseil sur une compétence mène aux formations.
    link: str | None = None


def _channel(fact: "Facts") -> str | None:
    application = fact.application
    if application.method == "ecrit":
        return "letter"
    if application.method != "electronique":
        return None
    if application.application_url:
        return "form"
    if application.contact_email:
        return "email"
    return None


def _silent(groups: dict[str, list["Facts"]]) -> tuple[str, int] | None:
    """Le groupe le plus grand, d'au moins `MIN_BASE` candidatures, sans aucune réponse."""
    silent = [
        (key, len(facts))
        for key, facts in groups.items()
        if len(facts) >= MIN_BASE and not any(f.answered for f in facts)
    ]
    return max(silent, key=lambda found: (found[1], found[0]), default=None)


def channel_advice(facts: list["Facts"], names: dict[str, str], today: date) -> Advice | None:
    """Une façon de postuler, sinon un site, qui ne répond jamais alors que d'autres répondent.
    Sans aucune réponse nulle part, rien : « Ce qui bloque » le dit déjà."""
    settled = [f for f in facts if f.application.sent_at <= today - timedelta(days=SETTLED_DAYS)]
    if not any(f.answered for f in settled):
        return None
    by_channel: dict[str, list[Facts]] = {}
    by_site: dict[str, list[Facts]] = {}
    for fact in settled:
        channel = _channel(fact)
        if channel is not None:
            by_channel.setdefault(channel, []).append(fact)
        if fact.source not in ("manual", "spontaneous"):
            by_site.setdefault(fact.source, []).append(fact)
    found = _silent(by_channel)
    if found is not None:
        title, text = CHANNELS[found[0]]
        return Advice("channel", title, text, found[1], "applications")
    found = _silent(by_site)
    if found is not None:
        name = names.get(found[0], found[0])
        return Advice(
            "site", f"Les offres de {name} ne répondent pas", SITE_TEXT, found[1], "applications"
        )
    return None


def _missing(keywords: Any) -> set[str]:
    """Les compétences demandées par l'offre et absentes du profil (score-v2, `covered` faux)."""
    if not isinstance(keywords, list):
        return set()
    return {
        str(k["text"]).strip()
        for k in keywords
        if isinstance(k, dict) and k.get("covered") is False and str(k.get("text") or "").strip()
    }


def _profiled(keywords: Any) -> bool:
    return isinstance(keywords, list) and any(
        isinstance(k, dict) and k.get("covered") is not None for k in keywords
    )


async def skill_advice(session: AsyncSession, start: date | None, end: date) -> Advice | None:
    """La compétence absente du profil que demandent le plus d'offres retenues de la période."""
    query = (
        select(Evaluation.keywords_asks)
        .join(Offer, Offer.id == Evaluation.offer_id)
        .where(
            Evaluation.filter_passed.is_(True),
            Offer.spontaneous.is_(False),
            Offer.duplicate_of.is_(None),
            Offer.first_seen_at < datetime.combine(end + timedelta(days=1), time.min, LOCAL_TZ),
        )
    )
    if start is not None:
        query = query.where(Offer.first_seen_at >= datetime.combine(start, time.min, LOCAL_TZ))
    total = 0
    counts: Counter[str] = Counter()
    spelled: dict[str, Counter[str]] = {}
    for keywords in await session.scalars(query):
        # Seules les offres comparées à un profil comptent dans la base.
        if not _profiled(keywords):
            continue
        total += 1
        for text in {t.casefold(): t for t in _missing(keywords)}.values():
            key = text.casefold()
            counts[key] += 1
            spelled.setdefault(key, Counter())[text] += 1
    if not counts:
        return None
    key, count = max(counts.items(), key=lambda item: (item[1], item[0]))
    if count < MIN_BASE:
        return None
    skill = spelled[key].most_common(1)[0][0][:SKILL_MAX]
    return Advice(
        "skill",
        f"{skill} revient dans {count} offres sur {total}",
        SKILL_TEXT,
        total,
        "offers",
        "/bilan/formations?onglet=catalogue",
    )
