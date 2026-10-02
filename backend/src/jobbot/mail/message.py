"""Lecture d'un e-mail brut : en-têtes utiles et corps HTML / texte."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parseaddr


@dataclass(frozen=True)
class ParsedEmail:
    message_id: str
    subject: str | None
    sender: str
    sender_domain: str
    received_at: datetime
    html: str | None
    text: str | None


def _body(msg: EmailMessage, subtype: str) -> str | None:
    part = msg.get_body(preferencelist=(subtype,))
    if part is None or part.get_content_subtype() != subtype:
        return None
    try:
        content = part.get_content()
    except (LookupError, ValueError):
        payload = part.get_payload(decode=True)
        content = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else None
    return content if isinstance(content, str) else None


def _header(msg: EmailMessage, name: str) -> str | None:
    try:
        value = msg.get(name)
    except (ValueError, IndexError):
        return None
    return str(value).strip() if value is not None else None


def parse_email(raw: bytes, *, fallback_received: datetime) -> ParsedEmail:
    msg = message_from_bytes(raw, policy=policy.default)
    assert isinstance(msg, EmailMessage)

    message_id = _header(msg, "Message-ID") or f"<{hashlib.sha256(raw).hexdigest()}@jobbot.local>"
    sender = parseaddr(_header(msg, "From") or "")[1].lower()

    received_at = fallback_received
    date_header = msg.get("Date")
    parsed_date = getattr(date_header, "datetime", None)
    if isinstance(parsed_date, datetime):
        received_at = parsed_date if parsed_date.tzinfo else parsed_date.replace(tzinfo=UTC)

    return ParsedEmail(
        message_id=message_id,
        subject=_header(msg, "Subject"),
        sender=sender,
        sender_domain=sender.rpartition("@")[2],
        received_at=received_at,
        html=_body(msg, "html"),
        text=_body(msg, "plain"),
    )
