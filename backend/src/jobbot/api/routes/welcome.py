"""L'accueil après la première connexion (docs/66)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from jobbot import welcome
from jobbot.collect import public_search
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/welcome", tags=["welcome"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


Goal = Literal["job", "orp", "news"]


class WelcomeOut(BaseModel):
    status: Literal["pending", "postponed", "done"]
    step: int
    goal: Goal | None
    trade: str | None
    # Les postes visés lus dans le CV et gardés à l'accueil (docs/121 §A) : pour les alertes.
    roles: list[str] = Field(default_factory=list)


class WelcomeIn(BaseModel):
    step: Annotated[int | None, Field(ge=1, le=20)] = None
    goal: Goal | None = None
    trade: Annotated[str | None, Field(max_length=80)] = None
    roles: list[Annotated[str, Field(min_length=1, max_length=80)]] | None = Field(
        default=None, max_length=3
    )
    # « Plus tard » : Aujourd'hui, avec « Terminer mon accueil » ; reprise à la connexion.
    postponed: bool | None = None
    done: bool | None = None


def _out(value: dict[str, object]) -> WelcomeOut:
    goal = value.get("goal")
    trade = value.get("trade")
    step = value.get("step")
    roles = value.get("roles")
    return WelcomeOut(
        roles=[r for r in roles if isinstance(r, str)] if isinstance(roles, list) else [],
        status=welcome.status(value),
        step=step if isinstance(step, int) else 1,
        goal=goal if goal in ("job", "orp", "news") else None,
        trade=trade if isinstance(trade, str) else None,
    )


@router.get("", operation_id="getWelcome")
async def get_welcome(request: Request) -> WelcomeOut:
    async with _runtime(request).sessionmaker() as session:
        return _out(await welcome.state(session))


@router.put("", operation_id="saveWelcome")
async def save_welcome(request: Request, body: WelcomeIn) -> WelcomeOut:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        value = await welcome.save(session, body.model_dump(exclude_none=True))
    if body.done and not runtime.settings.demo:
        # Les premières offres (docs/104, 0.80.0) : la recherche publique de jobup, une fois.
        await public_search.request(runtime, first_only=True)
    return _out(value)
