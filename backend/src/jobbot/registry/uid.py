"""Registre IDE (UID) de l'Office fédéral de la statistique : service public, sans compte.

Recherche par nom d'entreprise ; on n'en garde que le nom, l'adresse et l'état (docs/12 §2.2).
Le service limite le nombre de requêtes par minute : l'appelant espace ses recherches.
"""

import xml.etree.ElementTree as ET
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from typing import Any
from xml.sax.saxutils import escape

import httpx

ENDPOINT = "https://www.uid-wse.admin.ch/V5.0/PublicServices.svc"
ACTION = "http://www.uid.admin.ch/xmlns/uid-wse/IPublicServices/Search"
USER_AGENT = "job-bot/0.7 (usage personnel)"
# Radiée du registre du commerce, ou entreprise inactive / supprimée dans le registre IDE.
_REMOVED_CR = {"2"}
_REMOVED_UID = {"6", "7"}


@dataclass(frozen=True)
class RegistryCompany:
    uid: str
    name: str
    street: str
    zip_code: str
    town: str
    canton: str
    active: bool

    @property
    def address(self) -> str:
        """Deux lignes, comme une adresse postale : rue et numéro, NPA localité."""
        street = self.street[:1].upper() + self.street[1:]
        return f"{street}\n{self.zip_code} {self.town}".strip()

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "address": self.address}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first(element: ET.Element, name: str) -> str:
    for child in element.iter():
        if _local(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def parse_response(xml: str) -> list[RegistryCompany]:
    root = ET.fromstring(xml)
    companies = []
    for item in root.iter():
        if _local(item.tag) != "uidEntitySearchResultItem":
            continue
        uid_id = _first(item, "uidOrganisationId")
        street = " ".join(x for x in (_first(item, "street"), _first(item, "houseNumber")) if x)
        companies.append(
            RegistryCompany(
                uid=f"CHE{uid_id}" if uid_id else "",
                name=_first(item, "organisationName"),
                street=street,
                zip_code=_first(item, "swissZipCode"),
                town=_first(item, "town"),
                canton=_first(item, "cantonAbbreviation"),
                active=_first(item, "commercialRegisterEntryStatus") not in _REMOVED_CR
                and _first(item, "uidregStatusEnterpriseDetail") not in _REMOVED_UID,
            )
        )
    return companies


def _envelope(name: str) -> str:
    return (
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
        ' xmlns:uid="http://www.uid.admin.ch/xmlns/uid-wse"'
        ' xmlns:u5="http://www.uid.admin.ch/xmlns/uid-wse/5"><s:Body><uid:Search>'
        "<uid:searchParameters><u5:uidEntitySearchParameters>"
        f"<u5:organisationName>{escape(name[:100])}</u5:organisationName>"
        "</u5:uidEntitySearchParameters></uid:searchParameters>"
        "</uid:Search></s:Body></s:Envelope>"
    )


async def http_search(name: str) -> list[RegistryCompany]:
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.post(
            ENDPOINT,
            content=_envelope(name).encode(),
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f'"{ACTION}"'},
        )
    # Trop de résultats ou nom invalide : réponse « Fault », traitée comme aucun résultat.
    if response.status_code == 500 and "Fault" in response.text:
        return []
    response.raise_for_status()
    return parse_response(response.text)


# Remplaçable en test : aucun appel réseau.
search: Callable[[str], Awaitable[list[RegistryCompany]]] = http_search
