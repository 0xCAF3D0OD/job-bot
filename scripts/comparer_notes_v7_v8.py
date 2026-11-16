"""Noter le même lot d'offres avec score-v7 et score-v8, et donner les deux notes côte à côte (PR #671).

Depuis la racine du dépôt, sur une branche qui contient score-v8, avec la clé de l'IA dans `.env` :

    cd backend && uv run python ../scripts/comparer_notes_v7_v8.py --limit 20

Le prompt score-v7 est lu dans git (`origin/main`, ou le dernier commit qui l'avait). Les deux notes sont
refaites maintenant, avec le même modèle, le même profil et la même annonce : seul le prompt change. Rien n'est
écrit dans les notes ; chaque appel est compté dans le plafond (finalité « compare »), comme `jobbot
score-compare`. Les offres sont les dernières notées du compte de l'exploitant (`--compte N` pour un autre).
`--essai` : sans clé et sans appel, pour vérifier que le script tourne.
"""

import argparse
import asyncio
import copy
import json
import subprocess
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from jobbot import accounts
from jobbot.db.models import Evaluation, Offer
from jobbot.llm.client import RawResult, Refused
from jobbot.llm.scoring import OUTPUT_SCHEMA, InvalidScore, parse_output, request_params
from jobbot.runtime import Runtime
from jobbot.scoring.compare import word
from jobbot.scoring.service import (
    active_profile,
    budget_state,
    make_client,
    offer_data,
    record_call,
)
from jobbot.settings import Settings

V7_PATH = "backend/src/jobbot/llm/prompts/score-v7.md"
BANDS = ["Loin", "À creuser", "Proche", "Très proche"]


def v7_instructions(ref: str) -> str:
    """score-v7.md dans `ref` ; s'il n'y est plus (PR fusionnée), dans le parent du commit qui l'a retiré."""
    shown = subprocess.run(["git", "show", f"{ref}:{V7_PATH}"], capture_output=True, text=True)
    if shown.returncode == 0:
        return shown.stdout
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True
    ).stdout.strip()
    last = subprocess.run(
        ["git", "rev-list", "-1", "HEAD", "--", V7_PATH],
        check=True,
        capture_output=True,
        text=True,
        cwd=top,
    ).stdout.strip()
    return subprocess.run(
        ["git", "show", f"{last}^:{V7_PATH}"], check=True, capture_output=True, text=True
    ).stdout


def v7_schema() -> dict[str, Any]:
    schema = copy.deepcopy(OUTPUT_SCHEMA)
    schema["properties"].pop("quotes", None)
    schema["required"] = [name for name in schema["required"] if name != "quotes"]
    return schema


class Fake:
    """`--essai` : aucun appel, chaque note est « sans note »."""

    async def score(self, params: dict[str, Any]) -> RawResult:
        raise Refused("essai sans clé")


async def run(limit: int, ref: str, essai: bool, compte: int | None = None) -> int:
    settings = Settings()
    if not essai and not settings.llm_configured:
        print("IA non configurée : JOBBOT_ANTHROPIC_API_KEY manque.")
        return 1
    old_text, old_schema = v7_instructions(ref), v7_schema()
    runtime = Runtime.create(settings)
    rows: list[tuple[str, int | None, int | None]] = []
    try:
        if compte is None:
            await accounts.act_as_owner(runtime.sessionmaker)
        else:
            accounts.set_current(compte)
        client = Fake() if essai else make_client(settings)
        async with runtime.sessionmaker() as session:
            profile = await active_profile(session)
            offers = list(
                (
                    await session.scalars(
                        select(Offer)
                        .join(Evaluation, Evaluation.offer_id == Offer.id)
                        .where(Evaluation.score.is_not(None))
                        .order_by(Evaluation.scored_at.desc())
                        .limit(limit)
                    )
                ).all()
            )
            _, _, rate = await budget_state(session, datetime.now(UTC))
        for offer in offers:
            data = offer_data(offer)
            new = request_params(settings.score_model, settings.llm_effort, profile, data)
            old = copy.deepcopy(new)
            old["system"][0]["text"] = old_text
            old["output_config"]["format"]["schema"] = old_schema
            scores: list[int | None] = []
            for params in (old, new):
                try:
                    raw = await client.score(params)
                    async with runtime.sessionmaker.begin() as session:
                        await record_call(session, raw, offer_id=None, rate=rate, purpose="compare")
                    scores.append(parse_output(raw.text, profile).score)
                except (Refused, InvalidScore):
                    scores.append(None)
            rows.append((offer.title, scores[0], scores[1]))
    finally:
        await runtime.dispose()

    def band(score: int) -> int:
        return BANDS.index(word(score))

    print("| Offre | v7 | v8 | Écart (points) | Mot v7 | Mot v8 | Crans |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    done = [(t, a, b) for t, a, b in rows if a is not None and b is not None]
    for title, a, b in rows:
        if a is None or b is None:
            print(
                f"| {title[:60]} | {a if a is not None else 'sans note'} | {b if b is not None else 'sans note'} | | | | |"
            )
            continue
        print(
            f"| {title[:60]} | {a} | {b} | {b - a:+d} | {word(a)} | {word(b)} | {abs(band(b) - band(a))} |"
        )
    if done:
        gap = sum(abs(b - a) for _, a, b in done) / len(done)
        moved = sum(band(a) != band(b) for _, a, b in done)
        far = sum(abs(band(b) - band(a)) > 1 for _, a, b in done)
        print(
            f"\n{len(done)} offres notées deux fois · écart moyen {gap:.1f} points · {moved} changent de mot · {far} bougent de plus d'un cran"
        )
    print(json.dumps({"offres": len(rows), "comparées": len(done)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--ref", default="origin/main", help="où lire score-v7.md dans git")
    parser.add_argument("--essai", action="store_true")
    parser.add_argument(
        "--compte", type=int, default=None, help="un autre compte que celui de l'exploitant (démo)"
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.limit, args.ref, args.essai, args.compte)))
