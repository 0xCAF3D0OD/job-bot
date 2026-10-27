"""Ce qui marche dans ta recherche (docs/42) : parcours, comparaisons et résumé pour l'ORP.

De simples comptes sur tes données, sans IA. Peu de données, pas de conclusion : un groupe
de moins de `ENOUGH` candidatures est signalé « trop peu pour conclure ».
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from statistics import median

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Contact,
    Evaluation,
    Interview,
    Offer,
    OfferLink,
    Profile,
    Site,
    Training,
    TrainingMark,
)
from jobbot.followups.remind import remind_on
from jobbot.letters.document import MONTHS
from jobbot.orp.service import load_target

ENOUGH = 5
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
class Bucket:
    """Un mois (ou une semaine) de la période : candidatures envoyées et leurs réponses."""

    start: date
    applications: int = 0
    responses: int = 0


@dataclass
class Highlight:
    """« À retenir » d'Aujourd'hui (1.6.51, docs/interface.md n° 17) : le même écart que la
    phrase du Bilan, en un mot très grand et une phrase."""

    word: str
    sentence: str


@dataclass
class Insights:
    funnel: Funnel
    delay: Delay | None
    comparisons: list[Comparison]
    headline: str | None
    unit: str = "month"
    highlight: Highlight | None = None
    buckets: list[Bucket] = field(default_factory=list)
    interviews_upcoming: int = 0


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
        elif remind_on(fact.application) <= today:
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
        Comparison(
            "score",
            "Proximité avec le profil",
            sorted(by_score.values(), key=lambda g: order[g.key]),
        ),
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


def _widest(comparisons: list[Comparison]) -> tuple[str, Group, Group] | None:
    """L'écart le plus net : au moins le double, avec assez de candidatures des deux côtés et au
    moins 2 réponses du meilleur côté. La comparaison, le meilleur groupe, le moins bon."""
    best: tuple[float, tuple[str, Group, Group]] | None = None
    for comparison in comparisons:
        groups = [g for g in comparison.groups if g.enough]
        if len(groups) < 2:
            continue
        top = max(groups, key=lambda g: g.rate)
        bottom = min(groups, key=lambda g: g.rate)
        if top is bottom or top.responses < 2 or top.rate < 2 * bottom.rate:
            continue
        ratio = top.rate / bottom.rate if bottom.rate else float("inf")
        if best is None or ratio > best[0]:
            best = (ratio, (comparison.key, top, bottom))
    return best[1] if best else None


def headline(comparisons: list[Comparison]) -> str | None:
    """Une seule phrase, et seulement si un écart est net (`_widest`)."""
    found = _widest(comparisons)
    if found is None:
        return None
    _, top, bottom = found
    return (
        f"{top.subject} obtiennent plus souvent une réponse "
        f"({top.responses} sur {top.total}, contre {bottom.responses} sur {bottom.total})."
    )


def _word(key: str, group: Group) -> str:
    """Le mot de « À retenir » : le site, la note, le contact ou la relance qui marche le mieux."""
    if key == "source":
        if group.key == SPONTANEOUS:
            return "Spontanées"
        if group.key == MANUAL:
            return "Ajoutées à la main"
        return group.label
    if key == "score":
        return "Sans note" if group.key == "none" else f"Notées {group.label}"
    return group.label[0].upper() + group.label[1:]


def highlight(comparisons: list[Comparison]) -> Highlight | None:
    """« À retenir » : le même écart que `headline`, un mot et une phrase sans le répéter."""
    found = _widest(comparisons)
    if found is None:
        return None
    key, top, bottom = found
    other = bottom.subject[0].lower() + bottom.subject[1:]
    return Highlight(
        word=_word(key, top),
        sentence=(
            f"Plus souvent une réponse que {other} : {top.responses} sur {top.total}, "
            f"contre {bottom.responses} sur {bottom.total}."
        ),
    )


# « Tout » : les 12 derniers mois au plus dans « Par mois » (docs/55).
MAX_MONTHS = 12


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _next_month(day: date) -> date:
    return date(day.year + day.month // 12, day.month % 12 + 1, 1)


def buckets(facts: list[Facts], start: date | None, end: date, unit: str) -> list[Bucket]:
    """Candidatures par mois (ou par semaine du lundi, coupée au mois choisi) ; les réponses
    sont celles des candidatures envoyées ce mois-là, comme dans le parcours."""
    if unit == "week":
        first = start or end
        starts = [first]
        monday = first - timedelta(days=first.weekday()) + timedelta(days=7)
        while monday <= end:
            starts.append(monday)
            monday += timedelta(days=7)
    else:
        sent = [f.application.sent_at for f in facts]
        first = _month_start(start or (min(sent) if sent else end))
        starts = []
        month = first
        while month <= end:
            starts.append(month)
            month = _next_month(month)
        starts = starts[-MAX_MONTHS:]
    found = [Bucket(s) for s in starts]
    for fact in facts:
        for bucket in reversed(found):
            if fact.application.sent_at >= bucket.start:
                bucket.applications += 1
                bucket.responses += int(fact.answered)
                break
    return found


async def insights(
    session: AsyncSession, start: date | None, end: date, unit: str = "month"
) -> Insights:
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
        highlight=highlight(comparisons),
        unit=unit,
        buckets=buckets(facts, start, end, unit),
        interviews_upcoming=sum(
            f.application.interview_at is not None
            and f.application.interview_at > datetime.now(UTC)
            for f in facts
        ),
    )


async def first_activity(session: AsyncSession) -> date | None:
    """Le premier jour d'activité du compte (1.6.62) : la première offre reçue ou la première
    candidature. Il borne « Par mois » et « Mois précédents » : rien avant l'inscription."""
    first_offer = await session.scalar(
        select(func.min(Offer.first_seen_at)).where(Offer.duplicate_of.is_(None))
    )
    first_sent = await session.scalar(select(func.min(Application.sent_at)))
    days = [first_sent] if first_sent else []
    if first_offer is not None:
        days.append(first_offer.astimezone(LOCAL_TZ).date())
    return min(days) if days else None


async def responses(session: AsyncSession, start: date, end: date) -> int:
    """Les réponses aux candidatures envoyées entre deux dates (la période d'avant, 1.6.62)."""
    return sum(f.answered for f in await _facts(session, start, end))


@dataclass
class MonthCount:
    month: str
    count: int


async def months(session: AsyncSession, first: date | None, today: date) -> list[MonthCount]:
    """« Par mois » (1.6.62) : les candidatures de chaque mois ORP, du mois de la première activité
    au mois en cours, les 12 derniers au plus."""
    start = _month_start(first or today)
    found: list[date] = []
    month = start
    while month <= today:
        found.append(month)
        month = _next_month(month)
    keys = [f"{m:%Y-%m}" for m in found[-MAX_MONTHS:]]
    counts = dict(
        (
            await session.execute(
                select(Application.orp_month, func.count())
                .where(Application.orp_month.in_(keys))
                .group_by(Application.orp_month)
            )
        ).all()
    )
    return [MonthCount(key, int(counts.get(key, 0))) for key in keys]


@dataclass
class InterviewLine:
    application_id: int
    company: str
    day: date
    kind: str | None
    # « upcoming » à venir, « rejected » pas retenu, « rated » ressenti noté, « done » passé.
    state: str
    rating: int | None = None


async def interview_lines(
    session: AsyncSession, start: date | None, end: date
) -> list[InterviewLine]:
    """Les entretiens de la période (1.6.62), le plus récent d'abord : date, entreprise, type, état.
    Un entretien à venir compte, même après la fin de la période."""
    now = datetime.now(UTC)
    query = select(Application).where(Application.interview_at.is_not(None))
    if start is not None:
        query = query.where(Application.interview_at >= _start_of(start))
    applications = list(await session.scalars(query.order_by(Application.interview_at.desc())))
    latest: dict[int, Interview] = {}
    for found in await session.scalars(
        select(Interview)
        .where(Interview.application_id.in_([a.id for a in applications]))
        .order_by(Interview.held_at, Interview.id)
    ):
        latest[found.application_id] = found
    lines = []
    for application in applications:
        at = application.interview_at
        assert at is not None
        if at > now:
            state = "upcoming"
        elif at.astimezone(LOCAL_TZ).date() > end:
            continue
        elif application.status == ApplicationStatus.REFUS:
            state = "rejected"
        elif application.id in latest:
            state = "rated"
        else:
            state = "done"
        review = latest.get(application.id)
        lines.append(
            InterviewLine(
                application_id=application.id,
                company=application.company,
                day=at.astimezone(LOCAL_TZ).date(),
                kind=review.kind if review else None,
                state=state,
                rating=review.rating if review and state == "rated" else None,
            )
        )
    return lines


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


# Ce que donnent les critères (docs/63 §2) : sur la période, les offres reçues, celles qui passent
# le filtre, et les raisons d'écart les plus fréquentes. Une offre écartée pour deux raisons
# compte dans les deux.
REASON_LABELS = {
    "locations": "lieu",
    "min_rate": "taux d'activité",
    "contract": "type d'offre",
    "language": "langue",
    "remote": "télétravail",
    "remote_region": "télétravail hors de Suisse",
    "banned_word": "mot exclu",
}


@dataclass
class FilterSummary:
    received: int
    retained: int
    reasons: list[tuple[str, str, int]]


async def filter_summary(session: AsyncSession, start: date, end: date) -> FilterSummary:
    offers = (
        select(func.count())
        .select_from(Offer)
        .where(
            Offer.spontaneous.is_(False),
            Offer.duplicate_of.is_(None),
            Offer.first_seen_at >= _start_of(start),
            Offer.first_seen_at < _start_of(end + timedelta(days=1)),
        )
    )
    received = int(await session.scalar(offers) or 0)
    retained = int(
        await session.scalar(
            offers.join(Evaluation, Evaluation.offer_id == Offer.id).where(
                Evaluation.filter_passed.is_(True)
            )
        )
        or 0
    )
    rows = (
        await session.execute(
            text(
                "select r->>'rule' as rule, count(distinct o.id) as n "
                "from offers o join evaluations e on e.offer_id = o.id, "
                "jsonb_array_elements(e.filter_reasons) r "
                "where e.filter_passed is false and o.spontaneous is false "
                "and o.duplicate_of is null and o.first_seen_at >= :start "
                "and o.first_seen_at < :end group by 1 order by 2 desc, 1"
            ),
            {"start": _start_of(start), "end": _start_of(end + timedelta(days=1))},
        )
    ).all()
    reasons = [(rule, REASON_LABELS.get(rule, rule), int(n)) for rule, n in rows]
    return FilterSummary(received, retained, reasons)
