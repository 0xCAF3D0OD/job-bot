"""La feuille rédigée par l'IA (docs/83 §3), sur demande : un message suivi et poli pour le
conseiller, construit seulement à partir des faits de la page.

L'IA reçoit le mois en bref, ce qui bloque et ce qui marche, ce qui manque, les questions
cochées et les obligations ; jamais ton nom, tes coordonnées, le lieu ni le nom du conseiller.
"""

from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources

from jobbot.db.models import OrpMeeting
from jobbot.llm.common import SONNET, call, check_budget, clean
from jobbot.orp import meeting as service
from jobbot.runtime import Runtime

MODEL = SONNET
MAX_TOKENS = 800
ESTIMATE_USD = Decimal("0.05")
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/orp-sheet-v1.md").read_text("utf-8")


class RedactionUnavailable(Exception):
    """Pas d'IA, plafond atteint, pas de rendez-vous, ou réponse refusée."""


def facts(prep: service.Preparation) -> str:
    def block(tag: str, lines: list[str]) -> str:
        body = "\n".join(f"- {clean(line)}" for line in lines)
        return f"<{tag}>\n{body}\n</{tag}>"

    missing = [
        f"{m.skill} : demandé dans {m.count} des {prep.offers} offres bien notées"
        + (f" (formation possible : {m.training_title})" if m.training_title else "")
        for m in prep.missing
    ]
    return "\n".join(
        [
            block("mois", prep.summaries),
            block("bloque", prep.blockers),
            block("marche", [prep.works] if prep.works else []),
            block("manque", missing),
            block("questions", [q.text for q in prep.questions if q.checked]),
            # Sans la ligne du rendez-vous : elle porte le lieu.
            block(
                "obligations",
                [
                    o.text
                    for o in prep.obligations
                    if not o.done and not o.text.startswith("Rendez-vous le ")
                ],
            ),
        ]
    )


async def write(runtime: Runtime) -> str:
    """Rédige la feuille du prochain rendez-vous, la garde, et la renvoie."""
    rate = await check_budget(runtime, ESTIMATE_USD, RedactionUnavailable)
    async with runtime.sessionmaker() as session:
        found = await service.next_meeting(session, datetime.now(UTC))
        if found is None:
            raise RedactionUnavailable("indique d'abord la date du rendez-vous")
        prep = await service.prepare(session)
    params = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": facts(prep)}],
    }
    raw, _ = await call(runtime, params, rate, purpose="orp_sheet", error=RedactionUnavailable)
    text = raw.text.strip().strip('"«» ').strip()
    if not text:
        raise RedactionUnavailable("réponse vide de l'IA")
    async with runtime.sessionmaker.begin() as session:
        stored = await session.get(OrpMeeting, found.id)
        if stored is not None:
            stored.sheet_text = text
    return text
