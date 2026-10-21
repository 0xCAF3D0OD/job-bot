"""« Cette note ne me correspond pas » (docs/114).

Une correction ne change jamais la note en cachette : elle devient soit un critère (lieu,
taux, contrat : le filtre s'en charge, sans IA), soit un bloc de profil proposé, que la
personne relit avant de l'ajouter. L'offre corrigée est alors renotée aussitôt ; les autres
le sont sur « Renoter » (docs/11 §3).
"""

import json
import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any, Literal

import anthropic
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import CONTRACT_KEYWORDS, ContractType, contains
from jobbot.core.normalize import normalize_text
from jobbot.db.models import ChunkKind, Evaluation, Offer, ProfileChunk, ScoreCorrection
from jobbot.filtering.service import load_criteria, run_filter, save_criteria
from jobbot.llm.client import Refused
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

Direction = Literal["high", "low"]
Reason = Literal[
    "not_my_trade",
    "not_my_level",
    "sector",
    "place_rate_contract",
    "my_trade",
    "have_experience",
    "sector_ok",
    "other",
]
# Les raisons proposées pour chaque sens (docs/114 §2).
REASONS: dict[str, tuple[str, ...]] = {
    "high": ("not_my_trade", "not_my_level", "sector", "place_rate_contract", "other"),
    "low": ("my_trade", "have_experience", "sector_ok", "other"),
}
ORIGIN = "correction"
PROMPT_VERSION = "correction-v1"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/correction-v1.md").read_text("utf-8")
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 300
ESTIMATE_USD = Decimal("0.003")
_ANSWER = re.compile(r"<reponse>\s*(\{.*\})\s*</reponse>", re.S)
_REASON_TEXT = {
    "not_my_trade": "ce n'est pas mon métier",
    "not_my_level": "pas mon niveau (trop junior ou trop senior)",
    "sector": "le secteur ne m'intéresse pas",
    "place_rate_contract": "le lieu, le taux ou le contrat",
    "my_trade": "c'est bien mon métier",
    "have_experience": "j'ai l'expérience demandée",
    "sector_ok": "le secteur me plaît",
    "other": "autre",
}


class CorrectionRefused(Exception):
    """Raison inconnue pour ce sens, ou offre introuvable."""


@dataclass
class Block:
    kind: str
    title: str
    content: str
    by_ai: bool = False


@dataclass
class CriteriaChange:
    """Un réglage proposé en un clic : `changes` s'ajoute aux critères actuels."""

    key: str
    label: str
    changes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposal:
    block: Block | None = None
    criteria: list[CriteriaChange] = field(default_factory=list)


def check(direction: str, reason: str) -> None:
    if reason not in REASONS.get(direction, ()):
        raise CorrectionRefused("raison inconnue pour ce sens")


# --- Lieu, taux, contrat : un critère -------------------------------------------------------


async def criteria_changes(session: AsyncSession, offer: Offer) -> list[CriteriaChange]:
    """Les réglages qu'on peut préremplir d'après l'offre ; le lieu se règle dans Profil."""
    criteria = await load_criteria(session)
    found: list[CriteriaChange] = []
    if offer.rate_max is not None and offer.rate_max < 100:
        minimum = min(100, (offer.rate_max // 10 + 1) * 10)
        if criteria.min_rate is None or criteria.min_rate < minimum:
            found.append(
                CriteriaChange("min_rate", f"Taux minimum {minimum} %", {"min_rate": minimum})
            )
    text = normalize_text(
        " ".join(x for x in (offer.title, offer.employment_type, offer.description) if x)
    )
    for contract in ContractType:
        if contract in criteria.excluded_types:
            continue
        if any(contains(text, normalize_text(k)) for k in CONTRACT_KEYWORDS[contract]):
            label = {
                ContractType.INTERNSHIP: "Écarter les stages",
                ContractType.APPRENTICESHIP: "Écarter les apprentissages",
                ContractType.TEMPORARY: "Écarter les postes temporaires",
                ContractType.FREELANCE: "Écarter les mandats indépendants",
            }[contract]
            found.append(
                CriteriaChange(
                    f"contract_{contract.value}",
                    label,
                    {"excluded_types": [*criteria.excluded_types, contract.value]},
                )
            )
    return found


async def apply_criteria(session: AsyncSession, changes: dict[str, Any]) -> None:
    criteria = await load_criteria(session)
    values: dict[str, Any] = {}
    if isinstance(changes.get("min_rate"), int):
        values["min_rate"] = max(10, min(100, int(changes["min_rate"])))
    if isinstance(changes.get("excluded_types"), list):
        allowed = {c.value: c for c in ContractType}
        values["excluded_types"] = tuple(
            allowed[v] for v in changes["excluded_types"] if v in allowed
        )
    if values:
        await save_criteria(session, replace(criteria, **values))


# --- Les autres raisons : un bloc de profil ------------------------------------------------


def template(direction: str, reason: str, offer: Offer, note: str | None) -> Block:
    """Le bloc sans IA : la raison de la personne, avec le titre de l'offre."""
    title = offer.title.strip()[:120]
    where = offer.company or title
    texts: dict[str, tuple[str, str, str]] = {
        "not_my_trade": (
            ChunkKind.REDHIBITOIRE,
            "Pas ce métier",
            f"Les postes comme « {title} » ne correspondent pas à mon métier.",
        ),
        "not_my_level": (
            ChunkKind.REDHIBITOIRE,
            "Pas ce niveau",
            f"Les postes du niveau de « {title} » ne me correspondent pas.",
        ),
        "sector": (
            ChunkKind.REDHIBITOIRE,
            "Pas ce secteur",
            f"Le secteur de « {where} » ne m'intéresse pas.",
        ),
        "my_trade": (
            ChunkKind.PREFERENCE,
            "C'est mon métier",
            f"Les postes comme « {title} » font partie de mon métier.",
        ),
        "have_experience": (
            ChunkKind.PREFERENCE,
            "J'ai cette expérience",
            f"J'ai l'expérience demandée pour des postes comme « {title} ».",
        ),
        "sector_ok": (
            ChunkKind.PREFERENCE,
            "Ce secteur me plaît",
            f"Le secteur de « {where} » m'intéresse.",
        ),
    }
    kind, head, content = texts.get(
        reason,
        (
            ChunkKind.REDHIBITOIRE if direction == "high" else ChunkKind.PREFERENCE,
            "À propos des offres comme celle-ci",
            f"Pour les postes comme « {title} » : la note était trop "
            f"{'haute' if direction == 'high' else 'basse'}.",
        ),
    )
    if note:
        content = f"{content} {note.strip()}"
    return Block(kind=kind, title=head, content=content[:600])


def request_params(
    direction: str, reason: str, offer: Offer, summary: str | None, note: str | None
) -> dict[str, Any]:
    def clean(value: str | None, limit: int) -> str:
        return " ".join((value or "").replace("<", " ").replace(">", " ").split())[:limit]

    sens = "trop haute" if direction == "high" else "trop basse"
    message = (
        f"<offre>\ntitre : {clean(offer.title, 200)}\nentreprise : {clean(offer.company, 120)}\n"
        f"poste : {clean(summary, 400)}\n</offre>\n"
        f"<correction>\nla note est {sens} ; raison : {_REASON_TEXT[reason]}"
        f"{' ; ' + clean(note, 200) if note else ''}\n</correction>"
    )
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": message}],
    }


def parse_answer(text: str) -> tuple[str, str] | None:
    matches = _ANSWER.findall(text)
    if not matches:
        return None
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None
    title = " ".join(str(data.get("title", "")).split())[:120] if isinstance(data, dict) else ""
    content = " ".join(str(data.get("content", "")).split())[:600] if isinstance(data, dict) else ""
    return (title, content) if title and content else None


async def draft_block(
    runtime: Runtime,
    direction: str,
    reason: str,
    offer: Offer,
    summary: str | None,
    note: str | None,
) -> Block:
    """Le bloc rédigé par l'IA (environ 0,001 $) ; sinon, le modèle simple."""
    simple = template(direction, reason, offer, note)
    settings = runtime.settings
    if not settings.llm_configured:
        return simple
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        return simple
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(request_params(direction, reason, offer, summary, note))
    except (Refused, anthropic.APIConnectionError):
        return simple
    except anthropic.APIStatusError as exc:
        log.warning("correction_draft_failed", problem=account_problem(exc) or exc.status_code)
        return simple
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=offer.id, rate=rate, purpose="correction")
    parsed = parse_answer(raw.text)
    if parsed is None:
        return simple
    return Block(kind=simple.kind, title=parsed[0], content=parsed[1], by_ai=True)


async def propose(
    runtime: Runtime, offer_id: int, direction: str, reason: str, note: str | None
) -> Proposal:
    check(direction, reason)
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise CorrectionRefused("offre introuvable")
        summary = await session.scalar(
            select(Evaluation.summary_role).where(Evaluation.offer_id == offer_id)
        )
        if reason == "place_rate_contract":
            return Proposal(criteria=await criteria_changes(session, offer))
    return Proposal(block=await draft_block(runtime, direction, reason, offer, summary, note))


# --- Appliquer -------------------------------------------------------------------------------


@dataclass
class Applied:
    chunk_id: int | None
    score: int | None


async def apply(
    runtime: Runtime,
    offer_id: int,
    direction: str,
    reason: str,
    note: str | None,
    block: Block | None,
    criteria: dict[str, Any] | None,
) -> Applied:
    """Enregistre la correction (une par offre), ajoute le bloc ou règle le critère, puis
    renote l'offre corrigée si un bloc a été ajouté."""
    check(direction, reason)
    async with runtime.sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise CorrectionRefused("offre introuvable")
        before = await session.scalar(
            select(Evaluation.score).where(Evaluation.offer_id == offer_id)
        )
        chunk_id: int | None = None
        if block is not None:
            chunk = ProfileChunk(
                kind=block.kind,
                title=block.title.strip()[:200],
                content=block.content.strip()[:2000],
                tags=[],
                active=True,
                origin=ORIGIN,
            )
            session.add(chunk)
            await session.flush()
            chunk_id = chunk.id
        if criteria:
            await apply_criteria(session, criteria)
        statement = insert(ScoreCorrection).values(
            offer_id=offer_id,
            direction=direction,
            reason=reason,
            note=(note or "").strip()[:200] or None,
            score_before=before,
            chunk_id=chunk_id,
            created_at=datetime.now(UTC),
        )
        await session.execute(
            statement.on_conflict_do_update(
                constraint="score_corrections_offer_key",
                set_={
                    "direction": statement.excluded.direction,
                    "reason": statement.excluded.reason,
                    "note": statement.excluded.note,
                    "score_before": statement.excluded.score_before,
                    "chunk_id": statement.excluded.chunk_id,
                    "created_at": statement.excluded.created_at,
                },
            )
        )
    if criteria:
        await run_filter(runtime)
    score = before
    if block is not None and runtime.settings.llm_configured:
        score = await scoring_service.score_offer(runtime, offer_id)
    log.info("score_corrected", direction=direction, reason=reason, block=chunk_id is not None)
    return Applied(chunk_id=chunk_id, score=score)
