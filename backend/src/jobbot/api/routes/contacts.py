"""Contacts dans l'entreprise (docs/31) : recherches déjà remplies et prises de contact."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import ColumnElement, or_, select

from jobbot.contacts import service
from jobbot.db.models import Application, Contact, Offer
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["contacts"])

Role = Literal["recruiter", "manager", "team", "alumni", "other"]
Channel = Literal["linkedin_invite", "linkedin_message", "email", "phone", "other"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int | None
    application_id: int | None
    name: str | None
    role: Role
    channel: Channel
    contacted_on: date
    answered_on: date | None
    note: str | None


class ContactIn(BaseModel):
    offer_id: int | None = None
    application_id: int | None = None
    name: Annotated[str, Field(max_length=120)] | None = None
    role: Role = "recruiter"
    channel: Channel = "linkedin_invite"
    contacted_on: date
    answered_on: date | None = None
    note: Annotated[str, Field(max_length=1000)] | None = None

    @field_validator("name", "note")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return (value or "").strip() or None


class SearchLinkOut(BaseModel):
    kind: Literal["recruiting", "team", "alumni"]
    label: str
    url: str


class ContactsPage(BaseModel):
    company: str
    searches: list[SearchLinkOut]
    # Site de l'entreprise, quand il est connu (annonce, recherche d'adresse, docs/14 §4).
    website: str | None
    contacts: list[ContactOut]


async def _page(
    runtime: Runtime, company: str, title: str, website: str | None, owner: ColumnElement[bool]
) -> ContactsPage:
    async with runtime.sessionmaker() as session:
        schools = await service.schools(session)
        rows = await session.scalars(select(Contact).where(owner).order_by(Contact.contacted_on))
        contacts = [ContactOut.model_validate(c) for c in rows]
    links = service.search_links(company, title, schools)
    return ContactsPage(
        company=company,
        searches=[SearchLinkOut(kind=link.kind, label=link.label, url=link.url) for link in links],
        website=website if website and website.startswith("https://") else None,
        contacts=contacts,
    )


@router.get("/offers/{offer_id}/contacts", operation_id="getOfferContacts")
async def offer_contacts(request: Request, offer_id: int) -> ContactsPage:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        application_id = await session.scalar(
            select(Application.id).where(Application.offer_id == offer_id)
        )
    owner = (
        or_(Contact.offer_id == offer_id, Contact.application_id == application_id)
        if application_id
        else Contact.offer_id == offer_id
    )
    return await _page(
        runtime, offer.company or "l'entreprise", offer.title, offer.company_website, owner
    )


@router.get("/applications/{application_id}/contacts", operation_id="getApplicationContacts")
async def application_contacts(request: Request, application_id: int) -> ContactsPage:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        application = await session.get(Application, application_id)
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        website = None
        if application.offer_id and (offer := await session.get(Offer, application.offer_id)):
            website = offer.company_website
    owner = (
        or_(Contact.application_id == application_id, Contact.offer_id == application.offer_id)
        if application.offer_id
        else Contact.application_id == application_id
    )
    return await _page(runtime, application.company, application.job_title, website, owner)


@router.post("/contacts", operation_id="addContact", status_code=status.HTTP_201_CREATED)
async def add_contact(request: Request, body: ContactIn) -> ContactOut:
    if body.offer_id is None and body.application_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "offre ou candidature requise")
    async with _runtime(request).sessionmaker.begin() as session:
        application_id = body.application_id
        offer_id = body.offer_id
        if offer_id is not None and application_id is None:
            application_id = await session.scalar(
                select(Application.id).where(Application.offer_id == offer_id)
            )
        if application_id is not None and offer_id is None:
            application = await session.get(Application, application_id)
            offer_id = application.offer_id if application else None
        contact = Contact(**body.model_dump(exclude={"offer_id", "application_id"}))
        contact.offer_id = offer_id
        contact.application_id = application_id
        session.add(contact)
        await session.flush()
        return ContactOut.model_validate(contact)


@router.put("/contacts/{contact_id}", operation_id="updateContact")
async def update_contact(request: Request, contact_id: int, body: ContactIn) -> ContactOut:
    async with _runtime(request).sessionmaker.begin() as session:
        contact = await session.get(Contact, contact_id)
        if contact is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "contact introuvable")
        for key, value in body.model_dump(exclude={"offer_id", "application_id"}).items():
            setattr(contact, key, value)
        await session.flush()
        return ContactOut.model_validate(contact)


@router.delete(
    "/contacts/{contact_id}", operation_id="deleteContact", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(request: Request, contact_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        contact = await session.get(Contact, contact_id)
        if contact is not None:
            await session.delete(contact)
