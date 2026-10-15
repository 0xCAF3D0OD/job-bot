"""Ce qui marche dans ta recherche (docs/42) : parcours, comparaisons et résumé pour l'ORP.

De simples comptes sur tes données, sans IA. Peu de données, pas de conclusion : un groupe
de moins de `ENOUGH` candidatures est signalé « trop peu pour conclure ».
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Contact,
    Evaluation,
    Offer,
    OfferLink,
    Profile,
    Site,
    Training,
    TrainingMark,
)
from jobbot.letters.document import MONTHS
from jobbot.orp.service import load_target

ENOUGH = 5
# Une relance se propose après 10 jours (docs/38) : plus tôt, « jamais relancée » ne dit rien.
FOLLOW_UP_AGE = timedelta(days=10)
ANSWERED = (ApplicationStatus.ENTRETIEN, ApplicationStatus.REFUS, ApplicationStatus.ENGAGEMENT)
MET = (ApplicationStatus.ENTRETIEN, ApplicationStatus.ENGAGEMENT)
SPONTANEOUS = "spontaneous"
MANUAL = "manual"


@dataclass
class Group:
    key: str
    label: str
    # Sujet de la phrase de tête : « Les offres de jobup obtiennent plus souvent… ».
    subject: str
    responses: int = 0
    total: int = 0

    @property
    def enough(self) -> bool:
        return self.total >= ENOUGH

    @property
    def rate(self) -> float:
        return self.responses / self.total if self.total else 0.0


@dataclass
class Comparison:
    key: str
    title: str
    groups: list[Group] = field(default_factory=list)


@dataclass
class Funnel:
    received: int
    retained: int
    applications: int
    responses: int
    interviews: int
    engagements: int


@dataclass
class Delay:
    typical: int
    shortest: int
    longest: int


@dataclass
class Insights:
    funnel: Funnel
    delay: Delay | None
    comparisons: list[Comparison]
    headline: str | None


@dataclass
class Facts:
    """Ce que la plateforme sait d'une candidature, pour la ranger dans les groupes."""

    application: Application
    source: str
    score: int | None
    contact: bool

    @property
    def answered(self) -> bool:
        return self.application.status in ANSWERED

    @property
    def met(self) -> bool:
        return self.application.interview_at is not None or self.application.status in MET


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time.min, LOCAL_TZ)


async def _facts(
    session: AsyncSession, start: date | None, end: date, *, month: str | None = None
) -> list[Facts]:
    query = select(Application)
    if month is not None:
        query = query.where(Application.orp_month == month)
    else:
        query = query.where(Application.sent_at <= end)
        if start is not None:
            query = query.where(Application.sent_at >= start)
    applications = list(await session.scalars(query.order_by(Application.sent_at)))
    offer_ids = {a.offer_id for a in applications if a.offer_id is not None}
    spontaneous = set(
        await session.scalars(select(Offer.id).where(Offer.id.in_(offer_ids), Offer.spontaneous))
    )
    scores: dict[int, int | None] = dict(
        (
            await session.execute(
                select(Evaluation.offer_id, Evaluation.score).where(
                    Evaluation.offer_id.in_(offer_ids)
                )
            )
        ).all()
    )
    # Le premier site où l'offre a été vue fait foi.
    sources: dict[int, str] = {}
    for linked, source in (
        await session.execute(
            select(OfferLink.offer_id, OfferLink.source)
            .where(OfferLink.offer_id.in_(offer_ids))
            .order_by(OfferLink.id)
        )
    ).all():
        sources.setdefault(linked, source)
    contacted: set[tuple[str, int | None]] = set()
    for for_application, for_offer in (
        await session.execute(select(Contact.application_id, Contact.offer_id))
    ).all():
        contacted.add(("a", for_application))
        contacted.add(("o", for_offer))
    facts = []
    for application in applications:
        offer_id = application.offer_id
        if offer_id is None:
            source = MANUAL
        elif offer_id in spontaneous:
            source = SPONTANEOUS
        else:
            source = sources.get(offer_id, MANUAL)
        contact = ("a", application.id) in contacted or (
            offer_id is not None and ("o", offer_id) in contacted
        )
        facts.append(Facts(application, source, scores.get(offer_id or 0), contact))
    return facts


async def _site_names(session: AsyncSession) -> dict[str, str]:
    names = {
        slug: name for slug, name in (await session.execute(select(Site.slug, Site.name))).all()
    }
    return {**names, SPONTANEOUS: "spontanée", MANUAL: "ajoutée à la main"}


def _source_subject(key: str, name: str) -> str:
    if key == SPONTANEOUS:
        return "Tes candidatures spontanées"
    if key == MANUAL:
        return "Tes candidatures ajoutées à la main"
    return f"Les offres de {name}"


def _score_band(score: int | None) -> tuple[str, str, str]:
    if score is None:
        return "none", "sans note", "Les offres sans note"
    if score >= 80:
        return "high", "80 et plus", "Les offres notées 80 et plus"
    if score >= 60:
        return "middle", "60 à 79", "Les offres notées de 60 à 79"
    return "low", "moins de 60", "Les offres notées moins de 60"


def _add(groups: dict[str, Group], key: str, label: str, subject: str, answered: bool) -> None:
    group = groups.setdefault(key, Group(key, label, subject))
    group.total += 1
    group.responses += int(answered)


def compare(facts: list[Facts], names: dict[str, str], today: date) -> list[Comparison]:
    by_source: dict[str, Group] = {}
    by_score: dict[str, Group] = {}
    by_contact: dict[str, Group] = {}
    by_follow_up: dict[str, Group] = {}
    for fact in facts:
        name = names.get(fact.source, fact.source)
        _add(by_source, fact.source, name, _source_subject(fact.source, name), fact.answered)
        # Sans annonce, pas de note : seules les offres reçues se comparent.
        if fact.source not in (MANUAL, SPONTANEOUS):
            _add(by_score, *_score_band(fact.score), fact.answered)
        if fact.contact:
            _add(
                by_contact,
                "with",
                "avec un contact",
                "Tes candidatures avec un contact dans l'entreprise",
                fact.answered,
            )
        else:
            _add(
                by_contact,
                "without",
                "sans contact",
                "Tes candidatures sans contact",
                fact.answered,
            )
        if fact.application.followed_up_at is not None:
            _add(by_follow_up, "yes", "relancées", "Tes candidatures relancées", fact.answered)
        elif fact.application.sent_at <= today - FOLLOW_UP_AGE:
            _add(
                by_follow_up,
                "no",
                "jamais relancées",
                "Tes candidatures jamais relancées",
                fact.answered,
            )
    order = {
        "high": 0,
        "middle": 1,
        "low": 2,
        "none": 3,
        "with": 0,
        "without": 1,
        "yes": 0,
        "no": 1,
    }
    return [
        Comparison(
            "source",
            "D'où vient l'offre",
            sorted(by_source.values(), key=lambda g: (-g.total, g.label)),
        ),
        Comparison("score", "Note de l'IA", sorted(by_score.values(), key=lambda g: order[g.key])),
        Comparison(
            "contact",
            "Contact dans l'entreprise",
            sorted(by_contact.values(), key=lambda g: order[g.key]),
        ),
        Comparison(
            "follow_up",
            "Relance (après 10 jours)",
            sorted(by_follow_up.values(), key=lambda g: order[g.key]),
        ),
    ]


def headline(comparisons: list[Comparison]) -> str | None:
    """Une seule phrase, et seulement si un écart est net : au moins le double, avec assez
    de candidatures des deux côtés et au moins 2 réponses du meilleur côté."""
    best: tuple[float, str] | None = None
    for comparison in comparisons:
        groups = [g for g in comparison.groups if g.enough]
        if len(groups) < 2:
            continue
        top = max(groups, key=lambda g: g.rate)
        bottom = min(groups, key=lambda g: g.rate)
        if top is bottom or top.responses < 2 or top.rate < 2 * bottom.rate:
            continue
        ratio = top.rate / bottom.rate if bottom.rate else float("inf")
        text = (
            f"{top.subject} obtiennent plus souvent une réponse "
            f"({top.responses} sur {top.total}, contre {bottom.responses} sur {bottom.total})."
        )
        if best is None or ratio > best[0]:
            best = (ratio, text)
    return best[1] if best else None


async def insights(session: AsyncSession, start: date | None, end: date) -> Insights:
    offers = (
        select(func.count())
        .select_from(Offer)
        .where(
            Offer.spontaneous.is_(False),
            Offer.duplicate_of.is_(None),
            Offer.first_seen_at < _start_of(end + timedelta(days=1)),
        )
    )
    if start is not None:
        offers = offers.where(Offer.first_seen_at >= _start_of(start))
    received = int(await session.scalar(offers) or 0)
    retained = int(
        await session.scalar(
            offers.join(Evaluation, Evaluation.offer_id == Offer.id).where(
                Evaluation.filter_passed.is_(True)
            )
        )
        or 0
    )
    facts = await _facts(session, start, end)
    delays = [
        (f.application.status_at - f.application.sent_at).days
        for f in facts
        if f.answered and f.application.status_at is not None
    ]
    delays = [d for d in delays if d >= 0]
    comparisons = compare(facts, await _site_names(session), end)
    return Insights(
        funnel=Funnel(
            received=received,
            retained=retained,
            applications=len(facts),
            responses=sum(f.answered for f in facts),
            interviews=sum(f.met for f in facts),
            engagements=sum(f.application.status == ApplicationStatus.ENGAGEMENT for f in facts),
        ),
        delay=Delay(round(median(delays)), min(delays), max(delays)) if delays else None,
        comparisons=comparisons,
        headline=headline(comparisons),
    )


def _count(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _names(facts: list[Facts]) -> str:
    return ", ".join(dict.fromkeys(f.application.company for f in facts))


async def orp_summary(session: AsyncSession, month: str) -> str:
    """Quelques lignes pour le rendez-vous ORP : des faits tirés de tes données, rien d'autre."""
    year, number = month.split("-")
    facts = await _facts(session, None, date.max, month=month)
    target = await load_target(session)
    parts = [f"{MONTHS['fr'][int(number) - 1].capitalize()} {year} :"]
    line = _count(len(facts), "candidature", "candidatures")
    if target:
        line += f" (objectif {target})"
    spontaneous = sum(f.source == SPONTANEOUS for f in facts)
    if spontaneous:
        line += f", dont {_count(spontaneous, 'spontanée', 'spontanées')}"
    parts.append(line + ".")
    if facts:
        answered = sum(f.answered for f in facts)
        met = [f for f in facts if f.met]
        hired = [f for f in facts if f.application.status == ApplicationStatus.ENGAGEMENT]
        news = [
            _count(answered, "réponse", "réponses")
            if answered
            else "aucune réponse pour l'instant",
            _count(len(met), "entretien", "entretiens") + f" ({_names(met)})"
            if met
            else "aucun entretien",
            _count(len(hired), "engagement", "engagements") + f" ({_names(hired)})"
            if hired
            else "pas encore d'engagement",
        ]
        sentence = ", ".join(news)
        parts.append(sentence[0].upper() + sentence[1:] + ".")
        names = await _site_names(session)
        plural = {SPONTANEOUS: "spontanées", MANUAL: "ajoutées à la main"}
        counts = Counter(f.source for f in facts).most_common()
        parts.append(
            "Sources : "
            + ", ".join(f"{plural.get(s, names.get(s, s))} {n}" for s, n in counts)
            + "."
        )
    trainings = await _trainings(session, month)
    if trainings:
        label = "Formation" if len(trainings) == 1 else "Formations"
        parts.append(f"{label} : {', '.join(trainings)}.")
    return " ".join(parts)


async def _trainings(session: AsyncSession, month: str) -> list[str]:
    first = date.fromisoformat(f"{month}-01")
    after = date(first.year + first.month // 12, first.month % 12 + 1, 1)
    rows = (
        await session.execute(
            select(Training.title, TrainingMark.status)
            .join(TrainingMark, TrainingMark.training_id == Training.id)
            .join(Profile, Profile.id == TrainingMark.profile_id)
            .where(Profile.is_main.is_(True))
            .where(
                (TrainingMark.status == "in_progress")
                | (
                    (TrainingMark.status == "done")
                    & (TrainingMark.done_at >= first)
                    & (TrainingMark.done_at < after)
                )
            )
            .order_by(Training.title)
        )
    ).all()
    return [f"{title} ({'terminée' if status == 'done' else 'en cours'})" for title, status in rows]
