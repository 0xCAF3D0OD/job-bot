"""Coût de la ligne « Pourquoi » (prompt cv-v2, Kevin 16.11.2026), mesuré avant sa mise en service.

`jobbot mesure-pourquoi --lancer` (ou `make mesure-pourquoi`) prépare 5 CV FICTIFS
(cv_measure_cases.json), chacun pour une offre fictive, une fois avec cv-v1 (en service) et une
fois avec cv-v2 (qui ajoute une raison par changement), même modèle et mêmes réglages que la
production. Aucune donnée de compte n'est lue : pas de base, rien d'écrit, aucun appel enregistré
dans `llm_calls`. L'appel est payé par la clé de l'IA, hors plafond mensuel. Le compte rendu
n'affiche que des chiffres : jetons et prix par CV, total, différence v1/v2, et le nombre de
raisons qui passent la vérification.
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources
from typing import Any, Protocol

from jobbot.llm import cv as cv_llm
from jobbot.llm.client import RawResult, Refused
from jobbot.llm.pricing import Usage, cost_usd
from jobbot.llm.scoring import InvalidScore, OfferData, ProfileChunkData


@dataclass(frozen=True)
class Case:
    chunks: list[ProfileChunkData]
    offer: OfferData


def _case(n: int, data: dict[str, Any]) -> Case:
    chunks = [
        ProfileChunkData(id=n * 100 + i, kind=kind, title=title, content=content)
        for i, (kind, title, content) in enumerate(data["blocks"], start=1)
    ]
    offer = OfferData(
        id=n,
        title=data["offer"]["title"],
        company=data["offer"]["company"],
        location="Lausanne",
        rate="100 %",
        employment_type="CDI",
        text=data["offer"]["text"],
        partial=False,
    )
    return Case(chunks, offer)


# Cinq parcours inventés, cinq annonces inventées : aucune personne ni entreprise réelle.
CASES: list[Case] = [
    _case(n, data)
    for n, data in enumerate(
        json.loads(
            resources.files("jobbot.llm").joinpath("cv_measure_cases.json").read_text("utf-8")
        ),
        start=1,
    )
]


class Client(Protocol):
    async def score(self, params: dict[str, Any]) -> RawResult: ...


@dataclass
class Run:
    usage: Usage
    usd: Decimal
    reasons: int = 0
    valid: int = 0


@dataclass
class Row:
    case: int
    v1: Run | None
    v2: Run | None


async def _one(client: Client, model: str, effort: str, case: Case, nxt: bool) -> Run | None:
    params = cv_llm.request_params(
        model, effort, case.chunks, case.offer, language=None, next_prompt=nxt
    )
    try:
        raw = await client.score(params)
        output = cv_llm.parse_output(raw.text, case.chunks)
    except (Refused, InvalidScore):
        return None
    run = Run(raw.usage, cost_usd(raw.model, raw.usage))
    if nxt:
        given = json.loads(raw.text).get("reasons") or []
        run.reasons = len(given)
        offer_text = f"{case.offer.title}\n{case.offer.text or ''}"
        run.valid = len(cv_llm.parse_reasons(raw.text, output, case.chunks, offer_text))
    return run


async def measure(client: Client, model: str, effort: str) -> list[Row]:
    rows = []
    for n, case in enumerate(CASES, start=1):
        rows.append(
            Row(
                n,
                await _one(client, model, effort, case, False),
                await _one(client, model, effort, case, True),
            )
        )
    return rows


def _tokens(u: Usage) -> int:
    return u.input_tokens + u.cache_read_tokens + u.cache_write_tokens


def report(rows: list[Row]) -> list[str]:
    lines = [
        f"Prompts : {cv_llm.PROMPT_VERSION} (en service) et {cv_llm.NEXT_VERSION} (mesuré)",
        "| CV | entrée v1 | sortie v1 | prix v1 ($) | entrée v2 | sortie v2 | prix v2 ($) "
        "| écart ($) | raisons valables |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    pairs = [(r.v1, r.v2) for r in rows if r.v1 and r.v2]
    for r in rows:
        if not (r.v1 and r.v2):
            lines.append(f"| {r.case} | échec | | | | | | | |")
            continue
        lines.append(
            f"| {r.case} | {_tokens(r.v1.usage)} | {r.v1.usage.output_tokens} | {r.v1.usd:.5f} "
            f"| {_tokens(r.v2.usage)} | {r.v2.usage.output_tokens} | {r.v2.usd:.5f} "
            f"| {r.v2.usd - r.v1.usd:+.5f} | {r.v2.valid} sur {r.v2.reasons} |"
        )
    if pairs:
        one = sum((a.usd for a, _ in pairs), Decimal(0))
        two = sum((b.usd for _, b in pairs), Decimal(0))
        out1 = sum(a.usage.output_tokens for a, _ in pairs)
        out2 = sum(b.usage.output_tokens for _, b in pairs)
        pct = f" ({(two - one) / one * 100:+.1f} %)" if one else ""
        valid = sum(b.valid for _, b in pairs)
        given = sum(b.reasons for _, b in pairs)
        lines += [
            f"Total ({len(pairs)} CV) : v1 {one:.5f} $ · v2 {two:.5f} $ · écart {two - one:+.5f} $"
            f"{pct}",
            f"Par CV : v1 {one / len(pairs):.5f} $ · v2 {two / len(pairs):.5f} $ · écart "
            f"{(two - one) / len(pairs):+.5f} $",
            f"Jetons de sortie : v1 {out1} · v2 {out2} · écart {out2 - out1:+d}",
            f"Raisons valables : {valid} sur {given}",
        ]
    return lines
