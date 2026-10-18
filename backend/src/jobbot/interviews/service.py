"""Enseignements des entretiens et conseils de l'IA (docs/23 §3).

Les enseignements se calculent sur la plateforme, sans IA. Les conseils de l'IA ne partent
que sur demande, avec les retours et les blocs de profil seulement (ni nom, ni coordonnées).
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib import resources
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Application, Evaluation, Interview, Offer, Setting
from jobbot.llm.common import SONNET, call, check_budget, clean, parse_reponse
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile

PREPARED_KEY = "interview_prepared"
COACH_KEY = "interview_coaching"
# Points « à préparer » ajoutés depuis le retour d'un entraînement (docs/75 §7).
EXTRA_KEY = "interview_to_prepare_extra"
MODEL = SONNET
MAX_TOKENS = 3_000
ESTIMATE_USD = Decimal("0.06")
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/coach-v1.md").read_text("utf-8")


@dataclass
class QuestionStat:
    text: str
    count: int = 0
    difficult: int = 0


@dataclass
class Note:
    company: str
    held_at: date | None
    text: str


@dataclass
class Insights:
    count: int = 0
    average_rating: float | None = None
    questions: list[QuestionStat] = field(default_factory=list)
    went_well: list[Note] = field(default_factory=list)
    went_badly: list[Note] = field(default_factory=list)
    to_prepare: list[tuple[str, bool]] = field(default_factory=list)
    missed_questions: list[Note] = field(default_factory=list)
    employer_feedback: list[Note] = field(default_factory=list)


async def _prepared(session: AsyncSession) -> set[str]:
    value = await session.scalar(select(Setting.value).where(Setting.key == PREPARED_KEY))
    return {v for v in value if isinstance(v, str)} if isinstance(value, list) else set()


async def insights(session: AsyncSession) -> Insights:
    rows = (
        await session.execute(
            select(Interview, Application.company)
            .join(Application, Application.id == Interview.application_id)
            .order_by(Interview.held_at.desc().nulls_last(), Interview.id.desc())
        )
    ).all()
    result = Insights(count=len(rows))
    if not rows:
        done = await _prepared(session)
        result.to_prepare = [(t, normalize_text(t) in done) for t in await _extra(session)]
        return result
    result.average_rating = round(sum(i.rating for i, _ in rows) / len(rows), 1)
    stats: dict[str, QuestionStat] = {}
    prepare: dict[str, str] = {}
    # Libellé d'une question : celui de sa première apparition (entretiens du plus ancien).
    for interview, _ in reversed(rows):
        for question in interview.questions or []:
            text = str(question.get("text", "")).strip()
            key = normalize_text(text)
            if not key:
                continue
            stat = stats.setdefault(key, QuestionStat(text))
            stat.count += 1
            stat.difficult += bool(question.get("difficult"))
    for interview, company in rows:
        for attr, target in (
            ("went_well", result.went_well),
            ("went_badly", result.went_badly),
            ("missed_questions", result.missed_questions),
            ("employer_feedback", result.employer_feedback),
        ):
            if value := getattr(interview, attr):
                target.append(Note(company, interview.held_at, value))
        for item in interview.to_prepare or []:
            prepare.setdefault(normalize_text(item), item)
    done = await _prepared(session)
    for item in await _extra(session):
        prepare.setdefault(normalize_text(item), item)
    # Les questions difficiles d'abord, puis les plus fréquentes.
    result.questions = sorted(stats.values(), key=lambda s: (-s.difficult, -s.count, s.text))
    result.to_prepare = [(text, key in done) for key, text in prepare.items()]
    return result


async def _extra(session: AsyncSession) -> list[str]:
    value = await session.scalar(select(Setting.value).where(Setting.key == EXTRA_KEY))
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


async def add_to_prepare(session: AsyncSession, text: str) -> None:
    """Range un point à travailler, tiré d'un entraînement, dans « À préparer »."""
    current = await _extra(session)
    if normalize_text(text) in {normalize_text(t) for t in current}:
        return
    value = [*current, text][-30:]
    await session.execute(
        insert(Setting)
        .values(key=EXTRA_KEY, value=value)
        .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
    )


async def set_prepared(session: AsyncSession, text: str, done: bool) -> None:
    current = await _prepared(session)
    key = normalize_text(text)
    current = current | {key} if done else current - {key}
    value = sorted(current)
    await session.execute(
        insert(Setting)
        .values(key=PREPARED_KEY, value=value)
        .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
    )


class CoachUnavailable(Exception):
    """IA non configurée, plafond atteint, compte indisponible ou rien à analyser."""


@dataclass
class Coaching:
    created_at: datetime
    application_id: int | None
    pistes: list[str]
    answers: list[dict[str, str]]
    questions_to_ask: list[str]


def parse_answer(text: str) -> tuple[list[str], list[dict[str, str]], list[str]] | None:
    data = parse_reponse(text)
    if data is None:
        return None

    def strings(values: Any, limit: int) -> list[str]:
        return (
            [" ".join(v.split()) for v in values if isinstance(v, str) and v.strip()][:limit]
            if isinstance(values, list)
            else []
        )

    answers = [
        {"question": " ".join(a["question"].split()), "answer": a["answer"].strip()}
        for a in data.get("answers") or []
        if isinstance(a, dict)
        and isinstance(a.get("question"), str)
        and isinstance(a.get("answer"), str)
    ][:6]
    return strings(data.get("pistes"), 6), answers, strings(data.get("questions_to_ask"), 3)


async def offer_context(
    session: AsyncSession, application_id: int | None, *, excerpt: int = 800
) -> str:
    """Le poste visé : intitulé, entreprise, puis le résumé de l'offre, ou un extrait de
    l'annonce ; vide sans candidature."""
    application = await session.get(Application, application_id) if application_id else None
    if application is None:
        return ""
    text = f"Poste : {application.job_title}\nEntreprise : {application.company}"
    if application.offer_id:
        evaluation = await session.scalar(
            select(Evaluation).where(Evaluation.offer_id == application.offer_id)
        )
        offer = await session.get(Offer, application.offer_id)
        if evaluation and evaluation.summary_role:
            text += f"\nLe poste : {evaluation.summary_role}"
            text += f"\nCe qu'il demande : {evaluation.summary_asks or '?'}"
        elif offer and (offer.description or offer.snippet):
            text += f"\nAnnonce : {(offer.description or offer.snippet or '')[:excerpt]}"
    return text


def profile_text(chunks: list[Any]) -> str:
    return "\n".join(f"- [{c.kind}] {c.title} : {c.content}" for c in chunks)


async def _context(session: AsyncSession, application_id: int | None) -> tuple[str, str, str]:
    profile = profile_text(await active_profile(session))
    rows = (
        await session.execute(
            select(Interview, Application.job_title)
            .join(Application, Application.id == Interview.application_id)
            .order_by(Interview.held_at.desc().nulls_last())
            .limit(15)
        )
    ).all()
    notes = []
    for i, job in rows:
        difficult = [q.get("text") for q in i.questions or [] if q.get("difficult")]
        parts = [f"Poste : {job}", f"type : {i.kind or '?'}", f"ressenti {i.rating}/5"]
        if difficult:
            parts.append("questions difficiles : " + " ; ".join(str(q) for q in difficult))
        for label, value in (
            ("a marché", i.went_well),
            ("n'a pas marché", i.went_badly),
            ("à préparer", "; ".join(i.to_prepare or [])),
            ("retour employeur", i.employer_feedback),
        ):
            if value:
                parts.append(f"{label} : {value}")
        notes.append("- " + " | ".join(parts))
    upcoming = await offer_context(session, application_id)
    return clean(profile)[:12000], clean("\n".join(notes))[:8000], clean(upcoming)[:2000]


async def coach(runtime: Runtime, application_id: int | None) -> Coaching:
    async with runtime.sessionmaker() as session:
        profile, notes, upcoming = await _context(session, application_id)
    rate = await check_budget(runtime, ESTIMATE_USD, CoachUnavailable)
    if not notes:
        raise CoachUnavailable("aucun retour d'entretien à analyser")
    content = f"<profil>\n{profile}\n</profil>\n<retours>\n{notes}\n</retours>"
    if upcoming:
        content += f"\n<prochain>\n{upcoming}\n</prochain>"
    params = {
        "model": SONNET,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
    }
    # L'appel est compté même si la réponse est illisible (docs/76 §5).
    raw, _ = await call(runtime, params, rate, purpose="coach", error=CoachUnavailable)
    parsed = parse_answer(raw.text)
    if parsed is None:
        raise CoachUnavailable("réponse illisible, réessaie")
    async with runtime.sessionmaker.begin() as session:
        coaching = Coaching(datetime.now(UTC), application_id, *parsed)
        value = {**coaching.__dict__, "created_at": coaching.created_at.isoformat()}
        await session.execute(
            insert(Setting)
            .values(key=COACH_KEY, value=value)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
        )
    return coaching


async def last_coaching(session: AsyncSession) -> Coaching | None:
    value = await session.scalar(select(Setting.value).where(Setting.key == COACH_KEY))
    if not isinstance(value, dict):
        return None
    try:
        return Coaching(
            created_at=datetime.fromisoformat(value["created_at"]),
            application_id=value.get("application_id"),
            pistes=list(value.get("pistes") or []),
            answers=list(value.get("answers") or []),
            questions_to_ask=list(value.get("questions_to_ask") or []),
        )
    except (KeyError, ValueError, TypeError):
        return None
