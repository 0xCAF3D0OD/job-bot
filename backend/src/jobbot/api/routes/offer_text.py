"""Compléter une offre déjà reçue : lire son annonce, ou coller son texte (fiche de l'offre).

Une offre venue d'une alerte n'a parfois que l'extrait, et sa note est provisoire. La lecture
suit celle de « Ajouter une offre » (docs/111) : balisage JobPosting, puis texte principal, le
robots.txt du site respecté, jamais une connexion ou un captcha contourné. Le texte collé est
nettoyé de la même façon. Dans les deux cas, l'offre est renotée tout de suite.
"""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from jobbot import accounts, manual_offers
from jobbot.auth.service import Window
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/offers", tags=["offers"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Offre inconnue"}}
READ_RESPONSES: dict[int | str, dict[str, Any]] = {
    **NOT_FOUND,
    429: {"description": "Trop de lectures : « Réessaie dans n minutes »"},
}

# « Lire l'annonce maintenant » charge une page chez un tiers : 1 lecture par offre toutes les
# 5 minutes, 20 par heure par compte (en mémoire, comme les autres limites de auth.service).
per_offer = Window(limit=1, period_s=300)
per_account = Window(limit=20, period_s=3600)


def _later(seconds: int) -> HTTPException:
    minutes = max(1, -(-seconds // 60))
    word = "minute" if minutes == 1 else "minutes"
    return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Réessaie dans {minutes} {word}.")


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class OfferTextOut(BaseModel):
    # Vrai : le texte complet est enregistré, la note refaite (ou à refaire sans IA).
    saved: bool
    # « page » : lue par son lien ; « collé » : collée sur la fiche.
    source: Literal["page", "collé"] | None = None
    score: int | None = None
    # Ce qui a empêché la lecture ; `paste` : proposer de coller le texte de l'annonce.
    problem: str | None = None
    paste: bool = False


class OfferTextIn(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=manual_offers.MAX_TEXT * 2)]

    @field_validator("text")
    @classmethod
    def _long_enough(cls, value: str) -> str:
        if len(" ".join(value.split())) < manual_offers.MIN_PASTED:
            raise ValueError(
                f"le texte de l'annonce fait au moins {manual_offers.MIN_PASTED} caractères"
            )
        return value


def _refused(exc: Exception) -> HTTPException:
    if isinstance(exc, manual_offers.NoAnnouncement):
        return HTTPException(status.HTTP_409_CONFLICT, "candidature spontanée : pas d'annonce")
    return HTTPException(status.HTTP_404_NOT_FOUND, "offre inconnue")


@router.post("/{offer_id}/read", operation_id="readOfferText", responses=READ_RESPONSES)
async def read(request: Request, offer_id: int) -> OfferTextOut:
    runtime = _runtime(request)
    try:
        # L'offre d'abord (404 pour un autre compte, C-4), puis les limites.
        await manual_offers.check_offer(runtime, offer_id)
    except (manual_offers.OfferNotFound, manual_offers.NoAnnouncement) as exc:
        raise _refused(exc) from None
    account = f"compte-{accounts.current()}"
    offer_key = f"{account}:{offer_id}"
    if wait := max(per_offer.wait(offer_key), per_account.wait(account)):
        raise _later(wait)
    per_offer.take(offer_key)
    per_account.take(account)
    try:
        score = await manual_offers.read_offer(runtime, offer_id)
    except (manual_offers.OfferNotFound, manual_offers.NoAnnouncement) as exc:
        raise _refused(exc) from None
    except manual_offers.ReadProblem as exc:
        return OfferTextOut(saved=False, problem=exc.message, paste=exc.paste)
    return OfferTextOut(saved=True, source="page", score=score)


@router.put("/{offer_id}/description", operation_id="pasteOfferText", responses=NOT_FOUND)
async def paste(request: Request, offer_id: int, body: OfferTextIn) -> OfferTextOut:
    runtime = _runtime(request)
    try:
        async with runtime.sessionmaker() as session:
            text = await manual_offers.clean_pasted(session, body.text)
        score = await manual_offers.save_description(runtime, offer_id, text, "collé")
    except (manual_offers.OfferNotFound, manual_offers.NoAnnouncement) as exc:
        raise _refused(exc) from None
    return OfferTextOut(saved=True, source="collé", score=score)
