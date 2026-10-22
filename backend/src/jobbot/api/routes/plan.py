"""La formule du compte et ce qui reste ce mois-ci (docs/125 §4) : pour la rubrique Compte
des Réglages et les descriptions au survol des actions IA (« 2 lettres sur 10 ce mois-ci »)."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from jobbot import accounts, plans
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["plan"])


class UsageOut(BaseModel):
    key: Literal["score", "letter", "cv", "chat", "practice"]
    label: str
    used: int
    # Vide : sans limite (l'exploitant).
    limit: int | None
    # Le message à la limite (« Les 10 lettres du mois sont utilisées : elles reviennent le
    # 1er novembre. »), le même que celui de l'API qui refuse.
    limit_text: str | None


class PlanOut(BaseModel):
    plan: Literal["essentiel", "plus"]
    # L'exploitant : rien n'est limité, la formule ne s'affiche pas.
    unlimited: bool
    resets_on: date
    plus_price_chf: int
    usage: list[UsageOut]
    # Les limites de chaque formule, pour les comparer.
    limits: dict[str, dict[str, int]]


@router.get("/plan", operation_id="getPlan")
async def get_plan(request: Request) -> PlanOut:
    runtime: Runtime = request.app.state.runtime
    async with runtime.sessionmaker() as session:
        usage = await plans.usage(session)
        return PlanOut(
            plan=await plans.plan_of(session),
            unlimited=await accounts.is_owner(session),
            resets_on=plans.resets_on(),
            plus_price_chf=plans.PLUS_PRICE_CHF,
            usage=[
                UsageOut(
                    key=u.key,
                    label=u.label,
                    used=u.used,
                    limit=u.limit,
                    limit_text=None if u.limit is None else str(plans.LimitReached(u.key, u.limit)),
                )
                for u in usage
            ],
            limits=plans.LIMITS,
        )
