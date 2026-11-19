"""« Tes droits » (§72r, §72t, §72v) : la page, ta situation, les règles de docs/droits."""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from jobbot.droits import regles
from jobbot.droits import service as droits
from jobbot.followups.service import local_today
from jobbot.orp.meeting import next_meeting
from jobbot.orp.service import load_target, month_counts
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/droits", tags=["droits"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class SituationIO(BaseModel):
    inscription: date | None = None
    mois: Literal["12_17", "18_21", "22_24"] | None = None
    age: Literal["moins_25", "25_54", "55_plus"] | None = None
    enfants: bool | None = None
    gain: Annotated[int, Field(ge=0, le=100_000)] | None = None
    touchees: Annotated[int, Field(ge=0, le=1_000)] | None = None
    vacances_prises: Annotated[int, Field(ge=0, le=500)] | None = None


class FiguresOut(BaseModel):
    total: int | None
    restants: int | None
    taux: int | None
    fin: date | None
    vacances_acquis: int | None
    vacances_disponibles: int | None
    avs: bool


class LineOut(BaseModel):
    title: str
    detail: str
    source: str


class TopicOut(BaseModel):
    key: str
    title: str
    phrase: str
    keyword: str
    keyword_sub: str
    keyword_missing: str | None = None
    keyword_sub_missing: str | None = None
    source_label: str
    verified: date
    action: str
    lines: list[LineOut]


class SourceOut(BaseModel):
    key: str
    name: str
    url: str


class DutiesOut(BaseModel):
    searches_title: str
    searches_phrase: str
    searches_count: int
    searches_target: int | None
    month: str
    meeting_title: str
    meeting_at: datetime | None
    holidays_title: str
    holidays_phrase: str


class DroitsOut(BaseModel):
    source_label: str
    verified: date
    texts: dict[str, str]
    figures: FiguresOut
    situation_complete: bool
    topics: list[TopicOut]
    duties: DutiesOut
    sources: list[SourceOut]


def _topic(rules: regles.Rules, key: str) -> TopicOut:
    section = rules.section(key)
    return TopicOut(
        key=key,
        title=section.get("Titre"),
        phrase=section.get("Phrase"),
        keyword=section.get("Mot-clé"),
        keyword_sub=section.get("Sous le mot-clé"),
        keyword_missing=section.fields.get("Mot-clé sans solde"),
        keyword_sub_missing=section.fields.get("Sous le mot-clé sans solde"),
        source_label=section.get("Source affichée"),
        verified=date.fromisoformat(section.get("Vérifié")),
        action=section.get("Action"),
        lines=[LineOut(**line.__dict__) for line in rules.lines(key)],
    )


@router.get("", operation_id="getDroits")
async def get_droits(request: Request) -> DroitsOut:
    rules = regles.load()
    today = local_today()
    month = f"{today:%Y-%m}"
    async with _runtime(request).sessionmaker() as session:
        situation = await droits.load(session)
        counts = await month_counts(session, month)
        target = await load_target(session)
        meeting = await next_meeting(session, datetime.now(UTC))
    figs = droits.figures(rules, situation)
    page = rules.section("page")
    duties = rules.section("devoirs")
    return DroitsOut(
        source_label=page.get("Source affichée"),
        verified=date.fromisoformat(page.get("Vérifié")),
        texts=dict(page.fields),
        figures=FiguresOut(**figs.__dict__),
        situation_complete=all(
            getattr(situation, name) is not None
            for name in ("inscription", "mois", "age", "enfants", "gain", "touchees")
        ),
        topics=[_topic(rules, key) for key in regles.TOPICS],
        duties=DutiesOut(
            searches_title=duties.get("Recherches"),
            searches_phrase=duties.get("Recherches phrase"),
            searches_count=counts.count,
            searches_target=target,
            month=month,
            meeting_title=duties.get("Rendez-vous"),
            meeting_at=meeting.starts_at if meeting else None,
            holidays_title=duties.get("Annoncer"),
            holidays_phrase=duties.get("Annoncer phrase"),
        ),
        sources=[
            SourceOut(key=key, name=name, url=url) for key, (name, url) in rules.sources.items()
        ],
    )


@router.get("/situation", operation_id="getDroitsSituation")
async def get_situation(request: Request) -> SituationIO:
    async with _runtime(request).sessionmaker() as session:
        found = await droits.load(session)
    return SituationIO(**found.__dict__)


@router.put("/situation", operation_id="saveDroitsSituation")
async def save_situation(request: Request, body: SituationIO) -> SituationIO:
    """Ta situation, gardée dans ton compte, jamais envoyée à l'IA (§72t). Champ vide : retiré."""
    async with _runtime(request).sessionmaker.begin() as session:
        await droits.save(session, droits.Situation(**body.model_dump()))
    async with _runtime(request).sessionmaker() as session:
        found = await droits.load(session)
    return SituationIO(**found.__dict__)
