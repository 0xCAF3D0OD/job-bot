"""S'entraîner à l'entretien (docs/75) : l'IA joue le recruteur, puis fait un retour.

Cinq questions, une relance au plus par question. La plateforme tient le compte des questions
et des relances ; l'IA ne choisit que la question et sa formulation. L'IA reçoit l'offre, les
blocs de profil, les questions difficiles et les points à préparer : jamais le nom de la
personne, ses coordonnées, ses contacts ni les noms des recruteurs notés dans ses retours.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources
from typing import Any, Literal, get_args

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import plans
from jobbot.db.models import Application, Evaluation, InterviewPractice, Profile
from jobbot.interviews import service as interviews
from jobbot.llm.common import SONNET, call, check_budget, clean, parse_reponse
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile

MODEL = SONNET
QUESTIONS = 5
RECRUITER_MAX_TOKENS = 400
FEEDBACK_MAX_TOKENS = 4_000
# Un entraînement complet : une douzaine d'échanges et le retour (docs/75 §9). Le départ est
# refusé s'il ne reste pas de quoi aller jusqu'au retour.
SESSION_ESTIMATE_USD = Decimal("0.30")
TURN_ESTIMATE_USD = Decimal("0.02")
FEEDBACK_ESTIMATE_USD = Decimal("0.06")
ANSWER_MAX = 4_000
# Les valeurs permises, une seule fois : les routes les reprennent (docs/76 §5).
Kind = Literal["rh", "manager", "technique"]
Tone = Literal["bienveillant", "exigeant"]
Language = Literal["fr", "en", "de"]
Level = Literal["solide", "a_preciser", "a_retravailler"]
KINDS: dict[str, str] = {"rh": "RH", "manager": "manager", "technique": "technique"}
TONES: dict[str, str] = {"bienveillant": "bienveillant", "exigeant": "exigeant"}
LANGUAGES: dict[str, str] = {"fr": "français", "en": "anglais", "de": "allemand"}
LEVELS: tuple[Level, ...] = get_args(Level)
# Un point « à travailler » rejoint la liste « À préparer », limitée à cette longueur.
POINT_MAX = 200
RECRUITER = resources.files("jobbot.llm").joinpath("prompts/recruiter-v1.md").read_text("utf-8")
FEEDBACK = (
    resources.files("jobbot.llm").joinpath("prompts/practice-feedback-v1.md").read_text("utf-8")
)
_WORDS: dict[Language, set[str]] = {
    "fr": {"le", "la", "les", "des", "vous", "et", "pour", "nous", "avec", "une", "du"},
    "en": {"the", "and", "you", "we", "with", "for", "our", "your", "will", "of", "to"},
    "de": {"und", "die", "der", "sie", "wir", "mit", "für", "ihre", "das", "zu", "bei"},
}


class PracticeUnavailable(Exception):
    """IA non configurée, plafond atteint, compte indisponible, réponse de l'IA refusée ou
    illisible, entraînement terminé, réponse vide, ou question du recruteur pas encore là."""


def as_kind(value: str | None) -> Kind | None:
    """Le type d'un entretien noté, s'il existe aussi pour l'entraînement."""
    for kind in get_args(Kind):
        if kind == value:
            return kind  # type: ignore[no-any-return]
    return None


def guess_language(text: str | None) -> Language:
    """La langue de l'annonce, d'après ses mots les plus courants ; le français par défaut."""
    words = re.findall(r"[a-zäöüéèàç]+", (text or "").lower())[:600]
    counts = {lang: sum(w in common for w in words) for lang, common in _WORDS.items()}
    best = max(counts, key=lambda lang: counts[lang])
    return best if counts[best] >= 5 and counts[best] > counts["fr"] else "fr"


@dataclass
class Context:
    poste: str
    manques: str
    difficiles: str
    profil: str


async def _context(session: AsyncSession, application_id: int | None) -> Context:
    poste = await interviews.offer_context(session, application_id, excerpt=3000)
    gaps: list[str] = []
    application = await session.get(Application, application_id) if application_id else None
    if application is not None and application.offer_id:
        evaluation = await session.scalar(
            select(Evaluation).where(Evaluation.offer_id == application.offer_id)
        )
        if evaluation:
            gaps += [
                str(k.get("text"))
                for k in evaluation.keywords_asks or []
                if isinstance(k, dict) and k.get("text") and not k.get("covered")
            ]
            gaps += [str(g) for g in evaluation.gaps or [] if isinstance(g, str)]
    if not poste:
        occupation = await session.scalar(select(Profile.occupation).where(Profile.is_main))
        poste = "Entretien type, sans offre précise."
        if occupation:
            poste += f" Métier visé : {occupation}."
    found = await interviews.insights(session)
    difficult = [f"- {q.text}" for q in found.questions if q.difficult][:8]
    difficult += [f"- à préparer : {text}" for text, done in found.to_prepare if not done][:6]
    return Context(
        poste=clean(poste)[:4000],
        manques=clean("\n".join(f"- {g}" for g in dict.fromkeys(gaps)))[:1500] or "(aucun)",
        difficiles=clean("\n".join(difficult))[:2500] or "(aucune)",
        profil=clean(interviews.profile_text(await active_profile(session)))[:12000]
        or "(profil vide)",
    )


def _setup(practice: InterviewPractice) -> str:
    return (
        f"Type : {KINDS.get(practice.kind, practice.kind)} ; "
        f"ton : {TONES.get(practice.tone, practice.tone)} ; "
        f"langue : {LANGUAGES.get(practice.language, practice.language)}"
    )


def _system(
    instructions: str, practice: InterviewPractice, context: Context
) -> list[dict[str, Any]]:
    data = (
        f"<entretien>\n{_setup(practice)}\n</entretien>\n<poste>\n{context.poste}\n</poste>\n"
        f"<manques>\n{context.manques}\n</manques>\n"
        f"<questions_difficiles>\n{context.difficiles}\n</questions_difficiles>\n"
        f"<profil>\n{context.profil}\n</profil>"
    )
    # Consignes et contexte ne changent pas d'un échange à l'autre : mis en cache.
    return [
        {"type": "text", "text": instructions},
        {"type": "text", "text": data, "cache_control": {"type": "ephemeral"}},
    ]


def transcript(turns: list[dict[str, Any]]) -> str:
    lines = []
    for turn in turns:
        number = turn.get("question")
        if turn.get("role") == "recruteur":
            label = f"Recruteur (question {number}{', relance' if turn.get('relance') else ''})"
        else:
            label = f"Candidat (question {number})"
        text = "(question passée)" if turn.get("skipped") else turn.get("text", "")
        lines.append(f"{label} : {clean(str(text))}")
    return "\n".join(lines)


def current_question(turns: list[dict[str, Any]]) -> int:
    return max((int(t.get("question") or 0) for t in turns), default=0)


def _relance_used(turns: list[dict[str, Any]], number: int) -> bool:
    return any(
        t.get("role") == "recruteur" and t.get("question") == number and t.get("relance")
        for t in turns
    )


def parse_turn(text: str) -> tuple[str, str] | None:
    data = parse_reponse(text)
    if data is None:
        return None
    action = str(data["action"]) if data.get("action") in ("relance", "fin") else "question"
    said = " ".join(str(data.get("text") or "").split())
    return (action, said[:800]) if said or action == "fin" else None


def parse_feedback(text: str, numbers: set[int]) -> dict[str, Any] | None:
    data = parse_reponse(text)
    if data is None:
        return None

    def string(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    questions = {}
    for item in data.get("questions") or []:
        if not isinstance(item, dict) or not isinstance(item.get("question"), int):
            continue
        number = item["question"]
        if number in numbers and number not in questions:
            questions[number] = {
                "question": number,
                "level": item.get("level") if item.get("level") in LEVELS else "a_preciser",
                "good": string(item.get("good")),
                "missing": string(item.get("missing")),
                "better": string(item.get("better")),
            }

    def strings(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        # Un point « à travailler » peut rejoindre « À préparer » : même longueur au plus.
        return [" ".join(v.split())[:POINT_MAX] for v in value if isinstance(v, str) and v.strip()][
            :3
        ]

    return {
        "questions": [questions[n] for n in sorted(questions)],
        "strengths": strings(data.get("strengths")),
        "work_on": strings(data.get("work_on")),
    }


async def _call(runtime: Runtime, params: dict[str, Any], rate: Decimal) -> tuple[str, Decimal]:
    raw, chf = await call(runtime, params, rate, purpose="practice", error=PracticeUnavailable)
    return raw.text, chf


async def _check(runtime: Runtime, estimate: Decimal) -> Decimal:
    return await check_budget(runtime, estimate, PracticeUnavailable)


async def _recruiter_turn(
    runtime: Runtime, practice: InterviewPractice, rate: Decimal, *, relance_allowed: bool
) -> tuple[dict[str, Any] | None, Decimal]:
    """Le recruteur parle : relance (si permise) ou question suivante ; None si c'est fini."""
    turns = list(practice.turns or [])
    number = current_question(turns)
    if number >= QUESTIONS and not relance_allowed:
        return None, Decimal(0)
    if number == 0:
        state = "Pose la question 1 sur 5."
    elif number >= QUESTIONS:
        state = (
            "C'était la dernière question. Relance une fois si la réponse est vague ; "
            'sinon réponds {"action": "fin", "text": "Merci, c\'est terminé."}.'
        )
    elif relance_allowed:
        state = (
            f"Relance une fois sur la question {number}, ou pose la question {number + 1} sur 5."
        )
    else:
        state = f"Pose la question {number + 1} sur 5 (pas de relance)."
    async with runtime.sessionmaker() as session:
        context = await _context(session, practice.application_id)
    params = {
        "model": MODEL,
        "max_tokens": RECRUITER_MAX_TOKENS,
        "system": _system(RECRUITER, practice, context),
        "messages": [
            {
                "role": "user",
                "content": f"<echanges>\n{transcript(turns) or '(début)'}\n</echanges>\n"
                f"<etat>{state}</etat>",
            }
        ],
    }
    text, chf = await _call(runtime, params, rate)
    parsed = parse_turn(text)
    if parsed is None:
        raise PracticeUnavailable("réponse illisible, réessaie")
    action, said = parsed
    # Après la cinquième question, seule une relance est possible ; sinon c'est fini.
    if action == "fin" or (action == "question" and number >= QUESTIONS):
        return None, chf
    relance = action == "relance" and relance_allowed and number > 0
    return {
        "role": "recruteur",
        "text": said,
        "question": number if relance else number + 1,
        "relance": relance,
    }, chf


async def start(
    runtime: Runtime, application_id: int | None, kind: str, tone: str, language: str
) -> int:
    rate = await _check(runtime, SESSION_ESTIMATE_USD)
    async with runtime.sessionmaker.begin() as session:
        # La formule (docs/125) : les séances du mois ; les questions d'une séance ne comptent pas.
        try:
            await plans.check(session, plans.PRACTICE)
        except plans.LimitReached as exc:
            raise PracticeUnavailable(str(exc)) from exc
        if application_id is not None and await session.get(Application, application_id) is None:
            raise LookupError("candidature introuvable")
        practice = InterviewPractice(
            application_id=application_id, kind=kind, tone=tone, language=language, turns=[]
        )
        session.add(practice)
        await session.flush()
        practice_id = practice.id
    try:
        await _advance(runtime, practice_id, rate, relance_allowed=False)
    except PracticeUnavailable:
        # Pas de question : rien à reprendre, l'entraînement n'a pas commencé (docs/76 §3).
        async with runtime.sessionmaker.begin() as session:
            await session.delete(await _load(session, practice_id))
        raise
    return practice_id


async def _load(
    session: AsyncSession, practice_id: int, *, lock: bool = False
) -> InterviewPractice:
    # Verrouillé le temps d'une écriture : deux envois simultanés ne se mélangent pas.
    practice = await session.get(InterviewPractice, practice_id, with_for_update=lock)
    if practice is None:
        raise LookupError("entraînement introuvable")
    return practice


async def _advance(
    runtime: Runtime, practice_id: int, rate: Decimal, *, relance_allowed: bool
) -> None:
    async with runtime.sessionmaker() as session:
        practice = await _load(session, practice_id)
        session.expunge(practice)
    turn, chf = await _recruiter_turn(runtime, practice, rate, relance_allowed=relance_allowed)
    async with runtime.sessionmaker.begin() as session:
        stored = await _load(session, practice_id, lock=True)
        stored.cost_chf = (stored.cost_chf or Decimal(0)) + chf
        current = list(stored.turns or [])
        # Un autre échange (envoi en double, « Terminer ») est passé entre-temps : on ne
        # rajoute rien.
        if stored.status != "en_cours" or (current and current[-1].get("role") == "recruteur"):
            return
        if turn is not None:
            stored.turns = [*current, turn]
    if turn is None:
        await _feedback(runtime, practice_id, rate)


def _estimate(turns: list[dict[str, Any]]) -> Decimal:
    """La réponse à la dernière question déclenche le retour, plus coûteux."""
    return FEEDBACK_ESTIMATE_USD if current_question(turns) >= QUESTIONS else TURN_ESTIMATE_USD


async def _candidate(runtime: Runtime, practice_id: int, text: str, skipped: bool) -> None:
    async with runtime.sessionmaker() as session:
        rate = await _check(runtime, _estimate(list((await _load(session, practice_id)).turns)))
    async with runtime.sessionmaker.begin() as session:
        practice = await _load(session, practice_id, lock=True)
        if practice.status != "en_cours":
            raise PracticeUnavailable("cet entraînement est terminé")
        turns = list(practice.turns or [])
        if not turns or turns[-1].get("role") != "recruteur":
            raise PracticeUnavailable("attends la question du recruteur")
        number = current_question(turns)
        turn = {"role": "candidat", "text": "" if skipped else text, "question": number}
        if skipped:
            turn["skipped"] = True
        practice.turns = [*turns, turn]
        relance_allowed = not skipped and not _relance_used(turns, number)
    await _advance(runtime, practice_id, rate, relance_allowed=relance_allowed)


async def retry(runtime: Runtime, practice_id: int) -> None:
    """Reprend après une erreur de l'IA : le recruteur n'avait pas encore répondu."""
    async with runtime.sessionmaker() as session:
        practice = await _load(session, practice_id)
        turns = list(practice.turns or [])
    rate = await _check(runtime, _estimate(turns))
    if practice.status != "en_cours" or (turns and turns[-1].get("role") == "recruteur"):
        return
    last = turns[-1] if turns else None
    number = current_question(turns)
    if number >= QUESTIONS:
        # Dernière question répondue : c'est le retour qui manquait (docs/76 §3).
        await _feedback(runtime, practice_id, rate)
        return
    relance_allowed = (
        last is not None and not last.get("skipped") and not _relance_used(turns, number)
    )
    await _advance(runtime, practice_id, rate, relance_allowed=relance_allowed)


async def answer(runtime: Runtime, practice_id: int, text: str) -> None:
    text = text.strip()[:ANSWER_MAX]
    if not text:
        raise PracticeUnavailable("réponse vide")
    await _candidate(runtime, practice_id, text, skipped=False)


async def skip(runtime: Runtime, practice_id: int) -> None:
    await _candidate(runtime, practice_id, "", skipped=True)


async def finish(runtime: Runtime, practice_id: int) -> None:
    """« Terminer et voir le retour », à tout moment après une réponse."""
    rate = await _check(runtime, FEEDBACK_ESTIMATE_USD)
    async with runtime.sessionmaker() as session:
        practice = await _load(session, practice_id)
        if practice.status != "en_cours":
            return
        if not any(
            t.get("role") == "candidat" and not t.get("skipped") for t in practice.turns or []
        ):
            raise PracticeUnavailable("réponds au moins à une question avant le retour")
    await _feedback(runtime, practice_id, rate)


async def _feedback(runtime: Runtime, practice_id: int, rate: Decimal) -> None:
    async with runtime.sessionmaker() as session:
        practice = await _load(session, practice_id)
        context = await _context(session, practice.application_id)
        turns = list(practice.turns or [])
    # Les questions restées sans réponse ne comptent pas.
    answered = {
        int(t["question"]) for t in turns if t.get("role") == "candidat" and t.get("question")
    }
    content = (
        f"<entretien>\n{_setup(practice)}\n</entretien>\n<poste>\n{context.poste}\n</poste>\n"
        f"<profil>\n{context.profil}\n</profil>\n<echanges>\n{transcript(turns)}\n</echanges>"
    )
    params = {
        "model": MODEL,
        "max_tokens": FEEDBACK_MAX_TOKENS,
        "system": [{"type": "text", "text": FEEDBACK}],
        "messages": [{"role": "user", "content": content}],
    }
    text, chf = await _call(runtime, params, rate)
    feedback = parse_feedback(text, answered)
    async with runtime.sessionmaker.begin() as session:
        stored = await _load(session, practice_id)
        stored.cost_chf = (stored.cost_chf or Decimal(0)) + chf
        if feedback is not None:
            stored.feedback = feedback
            stored.status = "termine"
    if feedback is None:
        raise PracticeUnavailable("retour illisible, réessaie « Terminer et voir le retour »")
