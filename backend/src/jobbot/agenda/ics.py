"""Fichiers d'agenda au format iCalendar (RFC 5545), écrits à la main : pas de dépendance.

Lignes en CRLF, repliées à 75 octets ; texte échappé (\\, ; , et retours à la ligne).
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

PRODID = "-//jobA1//Agenda//FR"


@dataclass(frozen=True)
class Event:
    uid: str
    summary: str
    start: datetime | date
    # Absente pour une journée entière (un jour).
    end: datetime | None = None
    description: str = ""
    url: str | None = None
    # Rappels avant le début (« P1D », « PT2H »…).
    alarms: tuple[str, ...] = field(default_factory=tuple)


def escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", "\\,")
        .replace("\r\n", "\n")
        .replace("\n", "\\n")
    )


def fold(line: str) -> list[str]:
    """Replie une ligne à 75 octets UTF-8 (les suites commencent par une espace)."""
    out: list[str] = []
    current = ""
    for char in line:
        limit = 75 if not out else 74
        if len((current + char).encode("utf-8")) > limit:
            out.append(current)
            current = char
        else:
            current += char
    out.append(current)
    return [out[0], *(" " + part for part in out[1:])]


def _utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _event(event: Event, stamp: datetime) -> list[str]:
    lines = ["BEGIN:VEVENT", f"UID:{event.uid}", f"DTSTAMP:{_utc(stamp)}"]
    if isinstance(event.start, datetime):
        end = event.end or event.start + timedelta(hours=1)
        lines += [f"DTSTART:{_utc(event.start)}", f"DTEND:{_utc(end)}"]
    else:
        lines += [
            f"DTSTART;VALUE=DATE:{event.start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{event.start + timedelta(days=1):%Y%m%d}",
            "TRANSP:TRANSPARENT",
        ]
    lines.append(f"SUMMARY:{escape(event.summary)}")
    if event.description:
        lines.append(f"DESCRIPTION:{escape(event.description)}")
    if event.url:
        lines.append(f"URL:{event.url}")
    for trigger in event.alarms:
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape(event.summary)}",
            f"TRIGGER:-{trigger}",
            "END:VALARM",
        ]
    lines.append("END:VEVENT")
    return lines


def calendar(events: list[Event], name: str = "jobA1", now: datetime | None = None) -> str:
    stamp = now or datetime.now(UTC)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(name)}",
        # Relu toutes les 4 heures par les agendas qui le respectent.
        "REFRESH-INTERVAL;VALUE=DURATION:PT4H",
        "X-PUBLISHED-TTL:PT4H",
    ]
    for event in events:
        lines += _event(event, stamp)
    lines.append("END:VCALENDAR")
    return "".join(part + "\r\n" for line in lines for part in fold(line))
