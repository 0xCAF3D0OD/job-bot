"""Ce que partagent les appels ponctuels à l'IA (pistes d'entretien, entraînement) : texte
nettoyé, réponse JSON entre `<reponse>`, plafond du mois et appel journalisé (docs/76 §5).

L'appel est enregistré avant toute lecture de la réponse : une réponse illisible coûte quand
même, et son coût compte dans le plafond.
"""

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import anthropic

from jobbot.llm.client import RawResult, Refused
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

SONNET = "claude-sonnet-5"
_ANSWER = re.compile(r"<reponse>\s*(\{.*\})\s*</reponse>", re.S)


def clean(value: str) -> str:
    """Les données envoyées ne peuvent pas fermer ni ouvrir une balise du message."""
    return value.replace("<", " ").replace(">", " ")


def parse_reponse(text: str) -> dict[str, Any] | None:
    """L'objet JSON de la dernière balise `<reponse>`, ou None."""
    matches = _ANSWER.findall(text)
    if not matches:
        return None
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


async def check_budget(runtime: Runtime, estimate: Decimal, error: type[Exception]) -> Decimal:
    """Refuse (avec `error`) sans IA ou si le plafond du mois ne couvre pas `estimate` ;
    renvoie le taux dollar → franc."""
    if not runtime.settings.llm_configured:
        raise error("IA non configurée (réglage d'installation, voir le README)")
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + estimate * rate > budget:
        raise error("plafond mensuel de l'IA atteint")
    return rate


async def call(
    runtime: Runtime,
    params: dict[str, Any],
    rate: Decimal,
    *,
    purpose: str,
    error: type[Exception],
) -> tuple[RawResult, Decimal]:
    """Un appel à l'IA, journalisé et compté ; renvoie la réponse et son coût en francs."""
    try:
        raw = await scoring_service.make_client(runtime.settings).score(params)
    except Refused:
        raise error("réponse refusée par l'IA") from None
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise error(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        chf = await record_call(session, raw, offer_id=None, rate=rate, purpose=purpose)
    return raw, chf
