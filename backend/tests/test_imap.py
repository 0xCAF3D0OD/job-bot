"""La boîte IMAP n'est jamais ouverte autrement qu'en lecture seule."""

import imaplib
from datetime import date
from typing import Any

import pytest

from jobbot.mail.imap import ImapMailbox, MailboxError, imap_date


class ReadOnlyIMAP:
    """Faux serveur : toute commande non prévue (STORE, COPY, EXPUNGE…) fait échouer le test."""

    def __init__(self, messages: dict[int, bytes], password: str = "bon") -> None:
        self.messages = messages
        self.password = password
        self.commands: list[tuple[Any, ...]] = []

    def __call__(self, host: str, port: int, timeout: float) -> "ReadOnlyIMAP":
        self.commands.append(("connect", host, port))
        return self

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"commande IMAP interdite : {name}")

    def login(self, user: str, password: str) -> tuple[str, list[bytes]]:
        if password != self.password:
            raise imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Invalid credentials")
        return "OK", [b"LOGIN completed"]

    def select(self, mailbox: str, readonly: bool = False) -> tuple[str, list[bytes]]:
        assert readonly is True, "le dossier doit être ouvert en lecture seule (EXAMINE)"
        self.commands.append(("select", mailbox, readonly))
        return "OK", [str(len(self.messages)).encode()]

    def uid(self, command: str, *args: Any) -> tuple[str, list[Any]]:
        self.commands.append(("uid", command, *args))
        if command == "SEARCH":
            return "OK", [b" ".join(str(u).encode() for u in self.messages)]
        if command == "FETCH":
            uid, spec = int(args[0]), args[1]
            assert "BODY.PEEK[" in spec, "lecture sans BODY.PEEK : marquerait l'e-mail comme lu"
            raw = self.messages[uid]
            if "HEADER.FIELDS" in spec:
                header = raw.split(b"\r\n\r\n", 1)[0]
                lines = [ln for ln in header.split(b"\r\n") if ln.lower().startswith(b"message-id")]
                raw = b"\r\n".join(lines) + b"\r\n\r\n"
            return "OK", [(f"{uid} (UID {uid} BODY[] {{{len(raw)}}}".encode(), raw), b")"]
        raise AssertionError(f"commande IMAP interdite : UID {command}")

    def logout(self) -> tuple[str, list[bytes]]:
        self.commands.append(("logout",))
        return "BYE", []


def _mailbox(server: ReadOnlyIMAP, password: str = "bon") -> ImapMailbox:
    return ImapMailbox(
        host="imap.example.com",
        port=993,
        user="alertes@example.com",
        password=password,
        folder="INBOX",
        factory=server,
    )


def _raw(message_id: str) -> bytes:
    return f"Message-ID: {message_id}\r\nSubject: test\r\n\r\ncorps".encode()


def test_imap_date_does_not_depend_on_locale() -> None:
    assert imap_date(date(2026, 10, 2)) == "02-Oct-2026"


def test_fetch_is_read_only_and_skips_known_messages() -> None:
    server = ReadOnlyIMAP({1: _raw("<a@x>"), 2: _raw("<b@x>"), 3: _raw("<c@x>")})
    emails = _mailbox(server).fetch_since(
        date(2026, 10, 1), limit=10, skip_message_ids=lambda ids: {"<b@x>"} & ids
    )
    assert [e.uid for e in emails] == [1, 3]
    assert ("select", '"INBOX"', True) in server.commands
    assert server.commands[-1] == ("logout",)
    full_fetches = [
        c for c in server.commands if c[:2] == ("uid", "FETCH") and c[3] == "(BODY.PEEK[])"
    ]
    assert [c[2] for c in full_fetches] == ["1", "3"]


def test_limit_and_newest_first() -> None:
    server = ReadOnlyIMAP({uid: _raw(f"<{uid}@x>") for uid in (1, 2, 3)})
    oldest = _mailbox(server).fetch_since(
        date(2026, 10, 1), limit=2, skip_message_ids=lambda _: set()
    )
    newest = _mailbox(server).fetch_since(
        date(2026, 10, 1), limit=2, skip_message_ids=lambda _: set(), newest_first=True
    )
    assert [e.uid for e in oldest] == [1, 2]
    assert [e.uid for e in newest] == [3, 2]


def test_auth_failure_hides_credentials() -> None:
    server = ReadOnlyIMAP({}, password="bon")
    with pytest.raises(MailboxError) as excinfo:
        _mailbox(server, password="mot-de-passe-faux").fetch_since(
            date(2026, 10, 1), limit=10, skip_message_ids=lambda _: set()
        )
    assert excinfo.value.kind == "auth"
    assert "mot-de-passe-faux" not in str(excinfo.value)
    assert "alertes@example.com" not in str(excinfo.value)
    assert server.commands[-1] == ("logout",)


def test_connection_failure() -> None:
    def refuse(host: str, port: int, timeout: float) -> None:
        raise ConnectionRefusedError("refusé")

    mailbox = ImapMailbox(
        host="imap.example.com", port=993, user="u", password="p", folder="INBOX", factory=refuse
    )
    with pytest.raises(MailboxError) as excinfo:
        mailbox.fetch_since(date(2026, 10, 1), limit=1, skip_message_ids=lambda _: set())
    assert excinfo.value.kind == "connection"
