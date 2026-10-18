"""Adresse d'une entreprise dans le registre IDE : propositions et choix (docs/12 §2.2)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import anthropic
import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from jobbot import accounts
from jobbot.core.normalize import normalize_location
from jobbot.db.models import Company, Offer
from jobbot.registry import uid
from jobbot.registry.service import (
    CACHE_FOR,
    Place,
    WebUnavailable,
    apply_address,
    choose,
    name_key,
    proposals,
    remember,
    web_lookup,
)
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
    # Faute de correspondance sûre : adresse trouvée sur Internet par l'IA (0.7.2).
    web_address: str | None = None
    web_source_url: str | None = None
    # Pourquoi la recherche sur Internet n'a pas été faite (IA non configurée, plafond…).
    web_unavailable: str | None = None


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
        shared = await accounts.writes_shared(session)
    # Ce qu'on sait de l'entreprise : le cache commun, ou ce qu'on vient de trouver. Un invité
    # n'écrit pas le cache commun (docs/78 §3.2) : le résultat vaut pour ses offres seulement.
    known = _Known.of(record)
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
            if shared:
                await remember(session, key, found, chosen, offer.company)
            if chosen:
                await apply_address(session, key, chosen.address)
        if shared:
            async with runtime.sessionmaker() as session:
                known = _Known.of(await session.get(Company, key))
        else:
            known = _Known(
                uid=chosen.uid if chosen else None,
                address=chosen.address if chosen else None,
                candidates=[c.as_dict() for c in proposals(offer.company, found)],
            )
    web_unavailable = None
    if known.uid is None and known.address is None and not known.web_searched:
        try:
            web_found = await web_lookup(
                runtime, key, offer.company, normalize_location(offer.location) or None
            )
        except WebUnavailable as exc:
            web_unavailable = str(exc)
        except (anthropic.APIError, httpx.HTTPError):
            web_unavailable = "IA momentanément indisponible"
        else:
            if web_found:
                known.address, known.source_url = web_found.address, web_found.source_url
                known.chosen_by = "web"
    from_web = known.chosen_by == "web"
    return AddressCandidates(
        web_address=known.address if from_web else None,
        web_source_url=known.source_url if from_web else None,
        web_unavailable=web_unavailable,
        chosen_uid=known.uid,
        candidates=[
            RegistryCandidate(**{k: c[k] for k in ("uid", "name", "address", "canton")})
            for c in known.candidates
        ],
    )


@dataclass
class _Known:
    uid: str | None = None
    address: str | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)
    chosen_by: str | None = None
    source_url: str | None = None
    web_searched: bool = False

    @classmethod
    def of(cls, record: Company | None) -> "_Known":
        if record is None:
            return cls()
        return cls(
            uid=record.uid,
            address=record.address,
            candidates=list(record.candidates),
            chosen_by=record.chosen_by,
            source_url=record.source_url,
            web_searched=record.web_looked_up_at is not None,
        )


@router.post(
    "/offers/{offer_id}/address-candidates/choose",
    operation_id="chooseAddressCandidate",
    responses={503: {"description": "Registre IDE injoignable"}},
)
async def choose_address(request: Request, offer_id: int, body: ChooseIn) -> ChosenAddress:
    """On choisit une proposition : elle vaut pour toutes les offres de cette entreprise du
    compte. Le cache des entreprises est commun : seul l'exploitant y écrit son choix, celui d'un
    autre compte ne s'impose pas aux autres (docs/69 §1)."""
    runtime = _runtime(request)
    offer = await _offer_company(runtime, offer_id)
    assert offer.company is not None
    key = name_key(offer.company)
    async with runtime.sessionmaker() as session:
        record = await session.get(Company, key)
    candidate = next(
        (c for c in (record.candidates if record else []) if c["uid"] == body.uid), None
    )
    if candidate is None and record is None:
        # Proposition faite à un invité, que le cache commun ne garde pas : on la redemande
        # au registre.
        try:
            found = await uid.search(offer.company)
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "registre IDE injoignable, réessayer"
            ) from None
        candidate = next(
            (c.as_dict() for c in proposals(offer.company, found) if c.uid == body.uid), None
        )
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "proposition introuvable")
    async with runtime.sessionmaker.begin() as session:
        record = await session.get(Company, key)
        if record is not None and await accounts.is_owner(session):
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
