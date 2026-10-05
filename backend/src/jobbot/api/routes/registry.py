"""Adresse d'une entreprise dans le registre IDE : propositions et choix (docs/12 §2.2)."""

from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from jobbot.core.normalize import normalize_location
from jobbot.db.models import Company, Offer
from jobbot.registry import uid
from jobbot.registry.service import CACHE_FOR, Place, apply_address, choose, name_key, remember
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["registry"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class RegistryCandidate(BaseModel):
    uid: str
    name: str
    address: str
    canton: str


class AddressCandidates(BaseModel):
    # La proposition retenue d'office (correspondance sûre) ou choisie, s'il y en a une.
    chosen_uid: str | None
    candidates: list[RegistryCandidate]


class ChooseIn(BaseModel):
    uid: str


class ChosenAddress(BaseModel):
    company_address: str
    company_address_source: str


async def _offer_company(runtime: Runtime, offer_id: int) -> Offer:
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
    if not offer.company or not name_key(offer.company):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "entreprise non indiquée")
    return offer


@router.get(
    "/offers/{offer_id}/address-candidates",
    operation_id="getAddressCandidates",
    responses={503: {"description": "Registre IDE injoignable"}},
)
async def get_address_candidates(request: Request, offer_id: int) -> AddressCandidates:
    """Propositions du registre IDE ; une recherche est faite si rien n'est en cache."""
    runtime = _runtime(request)
    offer = await _offer_company(runtime, offer_id)
    assert offer.company is not None
    key = name_key(offer.company)
    async with runtime.sessionmaker() as session:
        record = await session.get(Company, key)
    if record is None or record.looked_up_at < datetime.now(UTC) - CACHE_FOR:
        try:
            found = await uid.search(offer.company)
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "registre IDE injoignable, réessayer"
            ) from None
        chosen = choose(
            offer.company, found, Place(offer.canton, normalize_location(offer.location))
        )
        async with runtime.sessionmaker.begin() as session:
            await remember(session, key, found, chosen, offer.company)
            if chosen:
                await apply_address(session, key, chosen.address)
        async with runtime.sessionmaker() as session:
            record = await session.get(Company, key)
    assert record is not None
    return AddressCandidates(
        chosen_uid=record.uid,
        candidates=[
            RegistryCandidate(**{k: c[k] for k in ("uid", "name", "address", "canton")})
            for c in record.candidates
        ],
    )


@router.post("/offers/{offer_id}/address-candidates/choose", operation_id="chooseAddressCandidate")
async def choose_address(request: Request, offer_id: int, body: ChooseIn) -> ChosenAddress:
    """Kevin choisit une proposition : elle vaut pour toutes les offres de cette entreprise."""
    runtime = _runtime(request)
    offer = await _offer_company(runtime, offer_id)
    assert offer.company is not None
    key = name_key(offer.company)
    async with runtime.sessionmaker.begin() as session:
        record = await session.get(Company, key)
        candidate = next(
            (c for c in (record.candidates if record else []) if c["uid"] == body.uid), None
        )
        if record is None or candidate is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "proposition introuvable")
        record.uid, record.address, record.chosen_by = (
            candidate["uid"],
            candidate["address"],
            "manual",
        )
        await apply_address(session, key, candidate["address"])
        current = await session.get(Offer, offer_id)
        assert current is not None
        # L'offre affichée prend le choix même si elle avait une adresse d'une autre source.
        if current.company_address_source != "manual":
            current.company_address, current.company_address_source = (
                candidate["address"],
                "registry",
            )
        return ChosenAddress(
            company_address=current.company_address or candidate["address"],
            company_address_source=current.company_address_source or "registry",
        )
