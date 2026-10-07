"""Format ORP : preuves des recherches personnelles d'emploi (docs/09-export-orp.md).

Fonctions pures, sans base : une candidature devient une ligne du formulaire, puis un CSV.
"""

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Zurich")
DEFAULT_DUE_DAY = 5

METHOD = {
    "electronique": "électronique",
    "ecrit": "écrit",
    "telephone": "téléphone",
    "personnel": "en personne",
}
COLUMNS = (
    "Date",
    "Entreprise",
    "Adresse",
    "Personne de contact",
    "Téléphone",
    "Poste",
    "Taux",
    "Mode",
    "Assignée par l'ORP",
    "Résultat",
    "Lien de la candidature",
)


@dataclass(frozen=True)
class ApplicationData:
    id: int
    sent_at: date
    company: str
    company_address: str | None
    contact_name: str | None
    contact_phone: str | None
    job_title: str
    rate_text: str | None
    method: str
    assigned_by_orp: bool
    status: str
    status_reason: str | None
    interview_at: datetime | None
    application_url: str | None = None
    contact_email: str | None = None


@dataclass(frozen=True)
class OrpRow:
    application_id: int
    date: str
    company: str
    address: str
    contact: str
    phone: str
    job_title: str
    rate: str
    method: str
    assigned: str
    result: str
    url: str = ""
    # Champs indispensables manquants : la ligne est « à compléter ».
    missing: list[str] = field(default_factory=list)
    # Les champs dans l'ordre du formulaire de saisie de Job-Room (copier un à un).
    job_room: list["JobRoomField"] = field(default_factory=list)

    def values(self) -> list[str]:
        return [
            self.date,
            self.company,
            self.address,
            self.contact,
            self.phone,
            self.job_title,
            self.rate,
            self.method,
            self.assigned,
            self.result,
            self.url,
        ]


@dataclass(frozen=True)
class Address:
    street: str = ""
    number: str = ""
    po_box: str = ""
    postcode_city: str = ""


_PO_BOX = re.compile(r"\b(?:case postale|cp|postfach|casella postale)\s*(\d+)\b", re.I)
_POSTCODE_CITY = re.compile(r"^(?:CH-)?(\d{4})\s+(.+)$", re.I)
_NUMBER_LAST = re.compile(r"^(.*\D)\s+(\d+\s?[a-zA-Z]?(?:[-/]\d+[a-zA-Z]?)?)$")
_NUMBER_FIRST = re.compile(r"^(\d+\s?[a-zA-Z]?)\s*,?\s+(.+)$")


def split_address(text: str | None) -> Address:
    """« Chemin Malombré 10, 1206 Genève » → rue, n°, case postale, NPA et lieu (Job-Room)."""
    raw = [p.strip() for line in (text or "").splitlines() for p in line.split(",") if p.strip()]
    # « 12, rue de Lausanne » : le numéro seul se recolle à la rue qui suit.
    parts: list[str] = []
    for part in raw:
        if parts and re.fullmatch(r"\d+\s?[a-zA-Z]?", parts[-1]) and not _POSTCODE_CITY.match(part):
            parts[-1] = f"{parts[-1]} {part}"
        else:
            parts.append(part)
    street = number = po_box = postcode_city = ""
    for part in parts:
        if (box := _PO_BOX.search(part)) and not po_box:
            po_box = box.group(1)
        elif (place := _POSTCODE_CITY.match(part)) and not postcode_city:
            postcode_city = f"{place.group(1)} {place.group(2).strip()}"
        elif not street:
            if last := _NUMBER_LAST.match(part):
                street, number = last.group(1).strip(), last.group(2).replace(" ", "")
            elif first := _NUMBER_FIRST.match(part):
                number, street = first.group(1).replace(" ", ""), first.group(2).strip()
            else:
                street = part
    return Address(street, number, po_box, postcode_city)


@dataclass(frozen=True)
class JobRoomField:
    # Étape du formulaire Job-Room (« Comment avez-vous postulé ? »…).
    step: str
    label: str
    value: str
    # Case à cocher ou bouton à choisir plutôt qu'un texte à coller.
    choice: bool = False


JOB_ROOM_METHOD = {
    "electronique": "Par voie électronique",
    "ecrit": "Par lettre",
    "personnel": "Contact personnel",
    "telephone": "Par téléphone",
}


def job_room_result(status: str) -> str:
    if status == "engagement":
        return "Engagement"
    if status == "refus":
        return "Réponse négative"
    if status == "entretien":
        return "Entretien d'embauche + En suspens"
    return "En suspens"


def job_room_rate(rate_text: str | None) -> str:
    text = (rate_text or "").casefold()
    if "partiel" in text:
        return "A temps partiel"
    if "plein" in text or "100" in text:
        return "A plein temps"
    return ""


def job_room_fields(app: "ApplicationData") -> list[JobRoomField]:
    """Les champs dans l'ordre du formulaire de saisie de Job-Room (capture du 2026-10-07)."""
    address = split_address(app.company_address)
    when = "Quand avez-vous postulé ?"
    how = "Comment avez-vous postulé ?"
    where = "Auprès de quelle entreprise ?"
    what = "Pour quel poste ?"
    return [
        JobRoomField(when, "Date", f"{app.sent_at:%d.%m.%Y}"),
        JobRoomField(how, "Mode", JOB_ROOM_METHOD.get(app.method, app.method), choice=True),
        JobRoomField(where, "Entreprise", app.company),
        JobRoomField(where, "Rue", address.street),
        JobRoomField(where, "N°", address.number),
        JobRoomField(where, "Numéro de case postale", address.po_box),
        JobRoomField(where, "Pays", "Suisse", choice=True),
        JobRoomField(where, "NPA / Lieu", address.postcode_city),
        JobRoomField(where, "Personne contactée", app.contact_name or ""),
        JobRoomField(where, "Courriel", app.contact_email or ""),
        JobRoomField(where, "Numéro de téléphone", app.contact_phone or ""),
        JobRoomField(what, "Désignation du poste", app.job_title),
        JobRoomField(what, "Lien vers le formulaire en ligne", app.application_url or ""),
        JobRoomField(
            "Assignation par l'ORP ?",
            "Assignée",
            "Oui" if app.assigned_by_orp else "Non",
            choice=True,
        ),
        JobRoomField("Taux d'occupation", "Taux", job_room_rate(app.rate_text), choice=True),
        JobRoomField("Résultat", "Résultat", job_room_result(app.status), choice=True),
    ]


def result_text(status: str, reason: str | None, interview_at: datetime | None) -> str:
    """Statut de suivi → colonne « Résultat » (en suspens, engagement, refus + motif)."""
    if status == "engagement":
        return "engagement"
    if status == "refus":
        return f"refus : {reason}" if reason else "refus"
    if status == "entretien":
        if interview_at is not None:
            return f"en suspens (entretien le {interview_at.astimezone(LOCAL_TZ):%d.%m})"
        return "en suspens (entretien)"
    if status == "sans_reponse":
        return "en suspens (sans réponse)"
    return "en suspens"


def to_row(app: ApplicationData) -> OrpRow:
    # Sur une ligne : l'adresse peut avoir été saisie sur deux (rue, NPA localité).
    lines = (app.company_address or "").splitlines()
    address = ", ".join(p.strip() for p in lines if p.strip())
    return OrpRow(
        application_id=app.id,
        date=f"{app.sent_at:%d.%m.%Y}",
        company=app.company,
        address=address,
        contact=app.contact_name or "",
        phone=app.contact_phone or "",
        job_title=app.job_title,
        rate=app.rate_text or "",
        method=METHOD.get(app.method, app.method),
        assigned="oui" if app.assigned_by_orp else "non",
        result=result_text(app.status, app.status_reason, app.interview_at),
        url=app.application_url or "",
        missing=[] if address else ["adresse de l'entreprise"],
        job_room=job_room_fields(app),
    )


def to_csv(rows: list[OrpRow]) -> bytes:
    """Séparateur « ; » et BOM UTF-8 : Excel en Suisse l'ouvre directement."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow(row.values())
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def shift_month(month: str, delta: int) -> str:
    year, number = (int(x) for x in month.split("-"))
    index = year * 12 + number - 1 + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def due_date(month: str, due_day: int = DEFAULT_DUE_DAY) -> date:
    """Date limite de remise : le jour `due_day` du mois suivant."""
    year, number = (int(x) for x in shift_month(month, 1).split("-"))
    return date(year, number, due_day)
