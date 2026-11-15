"""Mesure des notes courtes (score-v9, Kevin, 15.11.2026) : avant de les garder, on vérifie ce
qu'elles coûtent et si l'IA les écrit bien.

`jobbot mesure-notes-courtes` prend les 20 dernières offres notées du compte de l'exploitant, toutes
sources. Sans `--lancer`, elle ne fait que les compter et estimer le coût, sans appel à l'IA. Avec
`--lancer`, elle les note de nouveau avec le prompt suivant (NEXT_VERSION), même modèle et mêmes
paramètres que la production, et compare avec le dernier appel de note de chaque offre
(`llm_calls`, purpose « score »).

Rien n'est écrit en base : toutes les lectures se font en transaction READ ONLY (la base refuse
toute écriture), aucun appel n'est enregistré dans `llm_calls`, et le texte des offres n'est
jamais journalisé. L'appel est payé par la clé du serveur, hors plafond mensuel.
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from jobbot import accounts
from jobbot.db.base import read_only
from jobbot.db.models import Evaluation, LlmCall, Offer
from jobbot.llm.client import Refused
from jobbot.llm.pricing import Usage, cost_usd
from jobbot.llm.scoring import (
    NEXT_VERSION,
    SHORT_MAX,
    InvalidScore,
    ProfileChunkData,
    parse_output,
    request_params,
)
from jobbot.runtime import Runtime
from jobbot.scoring import service

SAMPLE = 20
EXAMPLES = 5
# Un texte complet qui exprime un doute : sa forme courte doit finir par « ? ».
DOUBT = re.compile(
    r"\?|à vérifier|à confirmer|non précis|pas précis|non indiqu|pas indiqu|non mentionn"
    r"|pas mentionn|inconnu|incertain|peut-être|probablement|semble|flou|pas clair",
    re.IGNORECASE,
)


def expresses_doubt(text: str) -> bool:
    return DOUBT.search(text) is not None


def short_problem(text: str, short: str | None) -> str | None:
    """Pourquoi une forme courte n'est pas valide ; None si elle l'est."""
    if not short:
        return "absente ou vide"
    if len(short) > SHORT_MAX:
        return f"{len(short)} caractères (plus de {SHORT_MAX})"
    if expresses_doubt(text) and "?" not in short:
        return "doute sans « ? »"
    return None


@dataclass(frozen=True)
class Point:
    text: str
    short: str | None = None


@dataclass(frozen=True)
class Call:
    """Les jetons d'un appel ; le coût au prix d'un appel direct, pour comparer à l'identique (un
    lot coûte moitié prix pour les mêmes jetons)."""

    input_tokens: int
    output_tokens: int
    usd: Decimal


@dataclass
class Sample:
    offer: Offer
    version: str | None
    before_points: list[Point]
    before: Call | None


@dataclass
class Measured:
    sample: Sample
    after: Call | None = None
    after_points: list[Point] = field(default_factory=list)
    error: str | None = None


def _call(model: str, usage: Usage) -> Call:
    return Call(
        input_tokens=usage.input_tokens + usage.cache_read_tokens + usage.cache_write_tokens,
        output_tokens=usage.output_tokens,
        usd=cost_usd(model, usage),
    )


def _points(values: object) -> list[Point]:
    if not isinstance(values, list):
        return []
    return [
        Point(str(v["text"]), v.get("short") if isinstance(v.get("short"), str) else None)
        for v in values
        if isinstance(v, dict) and v.get("text")
    ]


async def gather(
    runtime: Runtime, limit: int = SAMPLE
) -> tuple[list[ProfileChunkData], list[Sample]]:
    """Les dernières offres notées du compte de l'exploitant et le dernier appel de note de
    chacune, lus en transaction READ ONLY."""
    with read_only():
        async with runtime.sessionmaker() as session:
            owner = await session.scalar(select(func.platform_owner()))
        if owner is None:
            return [], []
        accounts.set_current(int(owner))
        async with runtime.sessionmaker() as session:
            profile = await service.active_profile(session)
            rows = (
                await session.execute(
                    select(Offer, Evaluation)
                    .join(Evaluation, Evaluation.offer_id == Offer.id)
                    .where(Evaluation.score.is_not(None))
                    .order_by(Evaluation.scored_at.desc())
                    .limit(limit)
                )
            ).all()
            samples = []
            for offer, evaluation in rows:
                last = await session.scalar(
                    select(LlmCall)
                    .where(LlmCall.offer_id == offer.id, LlmCall.purpose == "score")
                    .order_by(LlmCall.created_at.desc())
                    .limit(1)
                )
                before = (
                    _call(
                        last.model,
                        Usage(
                            last.input_tokens,
                            last.cache_read_tokens,
                            last.cache_write_tokens,
                            last.output_tokens,
                        ),
                    )
                    if last is not None
                    else None
                )
                samples.append(
                    Sample(
                        offer=offer,
                        version=evaluation.prompt_version,
                        before_points=_points(evaluation.strengths) + _points(evaluation.gaps),
                        before=before,
                    )
                )
    return profile, samples


async def chf_rate(runtime: Runtime) -> Decimal:
    with read_only():
        async with runtime.sessionmaker() as session:
            _, _, rate = await service.budget_state(session, datetime.now(UTC))
    return rate


def estimate_usd(samples: list[Sample]) -> Decimal:
    """Le coût d'une note de plus par offre, d'après les derniers appels (prudent sinon)."""
    known = [s.before.usd for s in samples if s.before is not None]
    each = sum(known, Decimal(0)) / len(known) if known else service.ESTIMATE_USD
    return (each * len(samples)).quantize(Decimal("0.0001"))


async def measure(
    runtime: Runtime, profile: list[ProfileChunkData], samples: list[Sample]
) -> list[Measured]:
    """Note de nouveau chaque offre avec le prompt suivant ; n'écrit rien."""
    settings = runtime.settings
    client = service.make_client(settings)
    results = []
    for sample in samples:
        data = service.offer_data(sample.offer)
        params = request_params(
            settings.score_model, settings.llm_effort, profile, data, next_prompt=True
        )
        try:
            raw = await client.score(params)
        except Refused as exc:
            results.append(Measured(sample, error=f"refusé : {exc}"))
            continue
        measured = Measured(sample, after=_call(raw.model, raw.usage))
        try:
            output = parse_output(raw.text, profile, data.text)
        except InvalidScore as exc:
            measured.error = str(exc)
        else:
            measured.after_points = [Point(p.text, p.short) for p in output.strengths + output.gaps]
        results.append(measured)
    return results


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal(0)) / len(values) if values else Decimal(0)


def _gap(before: Decimal, after: Decimal, digits: str = "1", unit: str = "") -> str:
    diff = after - before
    pct = f" ({diff / before * 100:+.1f} %)" if before else ""
    return f"{diff.quantize(Decimal(digits)):+}{unit}{pct}"


def report(results: list[Measured], rate: Decimal) -> list[str]:
    """Le compte rendu de `--lancer`, ligne par ligne."""
    pairs: list[tuple[Call, Call]] = [
        (r.sample.before, r.after)
        for r in results
        if r.sample.before is not None and r.after is not None
    ]
    lines = [f"Prompt mesuré : {NEXT_VERSION}"]
    versions: dict[str, int] = {}
    for r in results:
        versions[r.sample.version or "?"] = versions.get(r.sample.version or "?", 0) + 1
    lines.append("Notes d'avant : " + ", ".join(f"{n} en {v}" for v, n in sorted(versions.items())))
    missing = len([r for r in results if r.sample.before is None])
    if missing:
        lines.append(f"{missing} offre(s) sans appel de note dans llm_calls : hors comparaison.")
    if pairs:
        for label, values in (
            ("Jetons d'entrée", [(b.input_tokens, a.input_tokens) for b, a in pairs]),
            ("Jetons de sortie", [(b.output_tokens, a.output_tokens) for b, a in pairs]),
        ):
            before = _mean([Decimal(b) for b, _ in values])
            after = _mean([Decimal(a) for _, a in values])
            lines.append(
                f"{label} moyens ({len(pairs)} offres) : {before:.0f} → {after:.0f}, "
                f"écart {_gap(before, after)}"
            )
        before_usd = _mean([b.usd for b, _ in pairs])
        after_usd = _mean([a.usd for _, a in pairs])
        lines.append(
            f"Coût moyen par offre (prix d'un appel direct) : {before_usd:.5f} $ → "
            f"{after_usd:.5f} $, écart {_gap(before_usd, after_usd, '0.00001', ' $')} "
            f"({before_usd * rate:.5f} → {after_usd * rate:.5f} CHF)"
        )
    total = [p for r in results for p in r.after_points]
    invalid = [(p, problem) for p in total if (problem := short_problem(p.text, p.short))]
    if total:
        valid = len(total) - len(invalid)
        lines.append(
            f"Formes courtes valides : {valid} sur {len(total)} ({valid / len(total):.0%}) ; "
            f"{SHORT_MAX} caractères au plus, « ? » quand le texte exprime un doute"
        )
    for point, problem in invalid:
        lines.append(f"  invalide ({problem}) : « {point.short or ''} » ← {point.text}")
    for r in results:
        if r.error:
            lines.append(f"Échec pour l'offre {r.sample.offer.id} : {r.error}")
    lines.append("")
    lines.append(f"{EXAMPLES} exemples avant / après :")
    shown = [r for r in results if r.after_points][:EXAMPLES]
    for number, r in enumerate(shown, start=1):
        lines.append(f"{number}. {r.sample.offer.title}")
        for point in r.sample.before_points[:3]:
            lines.append(f"   avant : {point.text}")
        for point in r.after_points[:3]:
            lines.append(f"   après : {point.text}")
            lines.append(f"           court : « {point.short or ''} »")
    return lines
