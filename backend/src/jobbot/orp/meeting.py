"""Préparer le rendez-vous ORP (docs/83) : une feuille pour le conseiller, tirée de tes données.

Sans IA : des comptes et des règles simples, écrites ici. Rien n'est envoyé à l'ORP.

- **Ton mois en bref** : le résumé du Bilan (docs/42 §3), pour le mois passé et le mois en cours.
- **Ce qui bloque** : sur 3 mois, ce qui n'obtient aucune réponse, et l'objectif manqué.
- **Ce qui te manque** : les compétences demandées par les offres bien notées et absentes de ton
  profil, avec une formation qui les couvre s'il y en a une.
- **Tes questions** : proposées d'après ta situation (financement, mesure, assignation, gain
  intermédiaire), à cocher ; tu peux en écrire d'autres.
- **Tes obligations** : les preuves à remettre, les assignations en cours, le rendez-vous.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ, due_date, shift_month
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Evaluation,
    Offer,
    OrpMeeting,
    OrpMonth,
    Training,
    TrainingMark,
)
from jobbot.insights.service import ENOUGH, _facts, _site_names, compare, headline, orp_summary
from jobbot.letters.document import MONTHS
from jobbot.orp.service import load_due_day, load_target

PERIOD = timedelta(days=90)
# Une offre « bien notée » : celle dont tu te sens proche (docs/73 : la note de l'IA).
GOOD_SCORE = 60
# Une compétence qui revient : au moins 3 offres, et les 5 premières seulement.
MISSING_MIN, MISSING_MAX = 3, 5
ASSIGNMENT_AGE = timedelta(days=60)
OPEN = (ApplicationStatus.EN_ATTENTE, ApplicationStatus.RELANCEE)


@dataclass
class Missing:
    skill: str
    count: int
    training_id: int | None = None
    training_title: str | None = None


@dataclass
class Question:
    key: str
    text: str
    checked: bool = False


@dataclass
class Obligation:
    text: str
    due: date | None = None
    done: bool = False


@dataclass
class MonthFacts:
    """Les chiffres d'un mois, en une ligne sur la page (docs/131) ; le texte va à la feuille."""

    month: str
    count: int
    target: int | None
    answered: int
    interviews: int


@dataclass
class Preparation:
    summaries: list[str]
    works: str | None
    blockers: list[str]
    missing: list[Missing]
    # Offres bien notées des 3 derniers mois : le dénominateur de « ce qui te manque ».
    offers: int
    questions: list[Question]
    obligations: list[Obligation] = field(default_factory=list)
    # Aucune candidature encore : la feuille le dit (docs/128 §3).
    has_applications: bool = True
    months: list[MonthFacts] = field(default_factory=list)


def _month_name(month: str) -> str:
    year, number = month.split("-")
    return f"{MONTHS['fr'][int(number) - 1]} {year}"


def _day(value: date) -> str:
    return f"{value.day} {MONTHS['fr'][value.month - 1]}"


async def next_meeting(session: AsyncSession, now: datetime) -> OrpMeeting | None:
    """Le prochain rendez-vous ; celui du jour reste « prochain » jusqu'au soir."""
    start_of_day = now.astimezone(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    return await session.scalar(
        select(OrpMeeting)
        .where(OrpMeeting.starts_at >= start_of_day)
        .order_by(OrpMeeting.starts_at)
        .limit(1)
    )


async def _blockers(session: AsyncSession, today: date) -> tuple[list[str], str | None]:
    facts = await _facts(session, today - PERIOD, today)
    blockers: list[str] = []
    answered = sum(f.answered for f in facts)
    if len(facts) >= 2 * ENOUGH and answered == 0:
        blockers.append(f"Aucune réponse en 3 mois, sur {len(facts)} candidatures.")
    comparisons = compare(facts, await _site_names(session), today)
    for comparison in comparisons:
        if comparison.key == "score":
            continue
        for group in comparison.groups:
            # Tout un groupe sans réponse, avec assez de candidatures pour le dire.
            if group.enough and group.responses == 0 and group.total < len(facts):
                blockers.append(f"{group.subject} : {group.total} envoyées, aucune réponse.")
    target = await load_target(session)
    if target:
        current = today.strftime("%Y-%m")
        for back in (2, 1):
            month = shift_month(current, -back)
            count = sum(1 for f in await _facts(session, None, date.max, month=month))
            if count < target:
                blockers.append(
                    f"{_month_name(month).capitalize()} : {count} candidatures, "
                    f"pour un objectif de {target}."
                )
    return blockers[:5], headline(comparisons)


def _covers(training: Training, skill: str) -> bool:
    wanted = skill.casefold()
    words = [training.title, training.description or "", *(training.tags or [])]
    return any(wanted in str(w).casefold() for w in words)


async def _missing(session: AsyncSession, now: datetime) -> tuple[list[Missing], int]:
    rows = (
        await session.execute(
            select(Evaluation.keywords_asks)
            .join(Offer, Offer.id == Evaluation.offer_id)
            .where(
                Evaluation.score >= GOOD_SCORE,
                Offer.first_seen_at >= now - PERIOD,
                Offer.duplicate_of.is_(None),
            )
        )
    ).all()
    counts: Counter[str] = Counter()
    names: dict[str, str] = {}
    for (asks,) in rows:
        seen = set()
        for ask in asks or []:
            text = str(ask.get("text", "")).strip() if isinstance(ask, dict) else ""
            if not text or ask.get("covered"):
                continue
            key = text.casefold()
            if key not in seen:
                seen.add(key)
                counts[key] += 1
                names.setdefault(key, text)
    found = [
        Missing(names[key], count) for key, count in counts.most_common() if count >= MISSING_MIN
    ][:MISSING_MAX]
    if found:
        # Une formation que tu suis ou envisages d'abord, puis le catalogue.
        followed = set(await session.scalars(select(TrainingMark.training_id)))
        trainings = sorted(
            await session.scalars(select(Training).where(Training.dismissed.is_(False))),
            key=lambda t: (t.id not in followed, t.id),
        )
        for item in found:
            match = next((t for t in trainings if _covers(t, item.skill)), None)
            if match is not None:
                item.training_id, item.training_title = match.id, match.title
    return found, len(rows)


async def _suggested(
    session: AsyncSession, now: datetime, blockers: list[str], missing: list[Missing]
) -> list[Question]:
    questions: list[Question] = []
    # Les formations payantes suivies ou envisagées, pas encore financées (docs/37 §2).
    marks = (
        await session.execute(
            select(Training.id, Training.title)
            .join(TrainingMark, TrainingMark.training_id == Training.id)
            .where(
                Training.price != "free",
                TrainingMark.status.in_(("interested", "in_progress")),
                TrainingMark.funding_status.is_distinct_from("accepted"),
            )
            .order_by(Training.title)
        )
    ).all()
    for training_id, title in marks:
        questions.append(
            Question(
                f"funding:{training_id}",
                f"Est-il possible de financer la formation « {title} » ?",
                True,
            )
        )
    for item in missing:
        if item.training_id is None:
            questions.append(
                Question(
                    f"missing:{item.skill.casefold()}",
                    f"Une formation en {item.skill} est-elle envisageable ? "
                    f"(demandé dans {item.count} offres)",
                )
            )
    if any(b.startswith("Aucune réponse en 3 mois") for b in blockers):
        questions.append(
            Question(
                "measure",
                "Une mesure est-elle possible (stage, cours, programme d'emploi temporaire) ?",
                True,
            )
        )
    assigned = (
        await session.execute(
            select(Application.id, Application.company, Application.job_title).where(
                Application.assigned_by_orp.is_(True),
                Application.sent_at >= (now - ASSIGNMENT_AGE).date(),
            )
        )
    ).all()
    for application_id, company, title in assigned:
        questions.append(
            Question(
                f"assignment:{application_id}",
                f"La suite de l'assignation chez {company} ({title}).",
                True,
            )
        )
    questions.append(
        Question(
            "intermediate",
            "Si je prends un emploi temporaire, comment déclarer un gain intermédiaire ?",
        )
    )
    return questions


def merge(suggested: list[Question], saved: list[dict[str, Any]]) -> list[Question]:
    """Les questions proposées, avec ce que tu as coché ou décoché, puis les tiennes."""
    kept = {str(q.get("key")): q for q in saved if isinstance(q, dict)}
    merged = []
    for question in suggested:
        if question.key in kept:
            question.checked = bool(kept[question.key].get("checked"))
        merged.append(question)
    for key, entry in kept.items():
        if key.startswith("custom:") and str(entry.get("text", "")).strip():
            merged.append(Question(key, str(entry["text"]).strip(), bool(entry.get("checked"))))
    return merged


async def _obligations(
    session: AsyncSession, today: date, meeting: OrpMeeting | None
) -> list[Obligation]:
    obligations: list[Obligation] = []
    due_day = await load_due_day(session)
    previous = shift_month(today.strftime("%Y-%m"), -1)
    submitted = await session.scalar(
        select(OrpMonth.submitted_at).where(OrpMonth.month == previous)
    )
    obligations.append(
        Obligation(
            f"Preuves de {_month_name(previous)} : à remettre au plus tard le "
            f"{_day(due_date(previous, due_day))}.",
            due_date(previous, due_day),
            submitted is not None,
        )
    )
    open_assignments = (
        await session.execute(
            select(Application.company, Application.sent_at).where(
                Application.assigned_by_orp.is_(True), Application.status.in_(OPEN)
            )
        )
    ).all()
    for company, sent in open_assignments:
        obligations.append(
            Obligation(
                f"Assignation chez {company}, candidature du {_day(sent)} : "
                "le résultat est à communiquer à ton conseiller."
            )
        )
    if meeting is not None:
        when = meeting.starts_at.astimezone(LOCAL_TZ)
        place = f", {meeting.place}" if meeting.place else ""
        obligations.append(
            Obligation(f"Rendez-vous le {_day(when.date())} à {when:%H:%M}{place}.", when.date())
        )
    return obligations


async def prepare(session: AsyncSession, now: datetime | None = None) -> Preparation:
    moment = now or datetime.now(UTC)
    today = moment.astimezone(LOCAL_TZ).date()
    current = today.strftime("%Y-%m")
    summaries = [
        await orp_summary(session, shift_month(current, -1)),
        await orp_summary(session, current),
    ]
    target = await load_target(session)
    months = []
    for month in (shift_month(current, -1), current):
        facts = await _facts(session, None, date.max, month=month)
        months.append(
            MonthFacts(
                month=month,
                count=len(facts),
                target=target,
                answered=sum(f.answered for f in facts),
                interviews=sum(f.met for f in facts),
            )
        )
    blockers, works = await _blockers(session, today)
    missing, offers = await _missing(session, moment)
    meeting = await next_meeting(session, moment)
    suggested = await _suggested(session, moment, blockers, missing)
    return Preparation(
        summaries=summaries,
        works=works,
        blockers=blockers,
        missing=missing,
        offers=offers,
        questions=merge(suggested, list(meeting.questions) if meeting else []),
        obligations=await _obligations(session, today, meeting),
        has_applications=bool(await session.scalar(select(select(Application.id).exists()))),
        months=months,
    )
