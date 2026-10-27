"""La recherche globale (série du 27.10, point 2) : dans tes offres, tes candidatures et tes
entreprises, rien d'autre (NN/g : chercher dans ses propres données). Trois groupes, trois
résultats au plus par groupe, et le total pour « Tout voir (N) »."""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import ColumnElement, and_, func, select

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Application, Evaluation, Offer
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["search"])
SHOWN = 3

# Accents retirés côté base, comme la recherche des Offres (sans extension unaccent).
_ACCENTED = "àâäáãåéèêëíìîïóòôöõúùûüçñÿ"
_PLAIN = "aaaaaaeeeeiiiiooooouuuucny"


class OfferHit(BaseModel):
    id: int
    title: str
    company: str | None
    location: str | None
    score: int | None


class ApplicationHit(BaseModel):
    id: int
    company: str
    job_title: str
    status: str
    sent_at: date
    interview_at: datetime | None
    orp_month: str | None


class CompanyHit(BaseModel):
    name: str
    offers: int
    applications: int


class OfferHits(BaseModel):
    items: list[OfferHit]
    total: int


class ApplicationHits(BaseModel):
    items: list[ApplicationHit]
    total: int


class CompanyHits(BaseModel):
    items: list[CompanyHit]
    total: int


class GlobalSearchOut(BaseModel):
    q: str
    offers: OfferHits
    applications: ApplicationHits
    companies: CompanyHits


def _plain(*columns: object) -> ColumnElement[str]:
    return func.translate(func.lower(func.concat_ws(" ", *columns)), _ACCENTED, _PLAIN)


def _escape(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _and(text: ColumnElement[str], words: list[str]) -> ColumnElement[bool]:
    """Tous les mots, dans n'importe quel ordre."""
    return and_(*(text.like(f"%{_escape(word)}%", escape="\\") for word in words))


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


@router.get("/search", operation_id="searchEverything")
async def search(
    request: Request, q: Annotated[str, Query(min_length=1, max_length=120)]
) -> GlobalSearchOut:
    words = normalize_text(q).split()[:8]
    empty = GlobalSearchOut(
        q=q,
        offers=OfferHits(items=[], total=0),
        applications=ApplicationHits(items=[], total=0),
        companies=CompanyHits(items=[], total=0),
    )
    if not words:
        return empty
    async with _runtime(request).sessionmaker() as session:
        offer_text = _plain(Offer.title, Offer.company, Offer.location)
        offer_where = [
            Offer.duplicate_of.is_(None),
            Offer.spontaneous.is_(False),
            _and(offer_text, words),
        ]
        offer_total = int(
            await session.scalar(select(func.count()).select_from(Offer).where(*offer_where)) or 0
        )
        offer_rows = (
            await session.execute(
                select(Offer, Evaluation.score)
                .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
                .where(*offer_where)
                .order_by(Evaluation.score.desc().nulls_last(), Offer.first_seen_at.desc())
                .limit(SHOWN)
            )
        ).all()
        app_text = _plain(Application.job_title, Application.company, Application.location)
        app_where = _and(app_text, words)
        app_total = int(
            await session.scalar(select(func.count()).select_from(Application).where(app_where))
            or 0
        )
        apps = list(
            await session.scalars(
                select(Application)
                .where(app_where)
                .order_by(Application.sent_at.desc(), Application.id.desc())
                .limit(SHOWN)
            )
        )
        # Entreprises : le nom seul, celles des offres et des candidatures réunies.
        company_word = _and(func.translate(func.lower(Offer.company), _ACCENTED, _PLAIN), words)
        offer_companies = dict(
            (
                await session.execute(
                    select(Offer.company, func.count())
                    .where(
                        Offer.company.is_not(None),
                        Offer.duplicate_of.is_(None),
                        company_word,
                    )
                    .group_by(Offer.company)
                )
            ).all()
        )
        app_word = _and(func.translate(func.lower(Application.company), _ACCENTED, _PLAIN), words)
        app_companies = dict(
            (
                await session.execute(
                    select(Application.company, func.count())
                    .where(app_word)
                    .group_by(Application.company)
                )
            ).all()
        )
    by_name: dict[str, CompanyHit] = {}
    for name, count in offer_companies.items():
        if not name:
            continue
        key = normalize_text(name)
        hit = by_name.setdefault(key, CompanyHit(name=name, offers=0, applications=0))
        hit.offers += int(count)
    for name, count in app_companies.items():
        key = normalize_text(name)
        hit = by_name.setdefault(key, CompanyHit(name=name, offers=0, applications=0))
        hit.applications += int(count)
    companies = sorted(by_name.values(), key=lambda c: (-(c.offers + c.applications), c.name))
    return GlobalSearchOut(
        q=q,
        offers=OfferHits(
            items=[
                OfferHit(
                    id=offer.id,
                    title=offer.title,
                    company=offer.company,
                    location=offer.location,
                    score=score,
                )
                for offer, score in offer_rows
            ],
            total=offer_total,
        ),
        applications=ApplicationHits(
            items=[
                ApplicationHit(
                    id=a.id,
                    company=a.company,
                    job_title=a.job_title,
                    status=a.status,
                    sent_at=a.sent_at,
                    interview_at=a.interview_at,
                    orp_month=a.orp_month,
                )
                for a in apps
            ],
            total=app_total,
        ),
        companies=CompanyHits(items=companies[:SHOWN], total=len(companies)),
    )
