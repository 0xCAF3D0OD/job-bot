"""Format ORP : preuves des recherches personnelles d'emploi (docs/09-export-orp.md).

Fonctions pures, sans base : une candidature devient une ligne du formulaire, puis un CSV.
"""

import csv
import io
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
    # Champs indispensables manquants : la ligne est « à compléter ».
    missing: list[str] = field(default_factory=list)

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
        missing=[] if address else ["adresse de l'entreprise"],
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
