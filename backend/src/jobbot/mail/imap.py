"""Lecture IMAP (docs/03-collecte-gmail.md §3, docs/113).

La lecture est strictement en lecture seule : le dossier est ouvert avec EXAMINE (select
readonly) et les messages sont lus avec BODY.PEEK, qui ne pose pas le drapeau « lu ». Dans la
boîte de l'exploitant, aucune commande d'écriture (STORE, COPY, MOVE, EXPUNGE, APPEND…) n'est
jamais envoyée : un test le vérifie.

Seule exception (docs/113) : la boîte des invités, qui appartient à la plateforme, est vidée
de ce qui est déjà copié dans jobA1 (`clean`) ; elle seule est créée « writable ».
"""

import imaplib
import re
import ssl
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from jobbot.settings import Settings

ErrorKind = Literal["auth", "connection", "other"]

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_MESSAGE_ID = re.compile(rb"^message-id:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


class MailboxError(Exception):
    """Erreur de boîte aux lettres ; le message ne contient jamais d'identifiants."""

    def __init__(self, kind: ErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class FetchedEmail:
    uid: int
    raw: bytes


def imap_date(day: date) -> str:
    """Date au format IMAP (01-Oct-2026), indépendante de la langue du système."""
    return f"{day.day:02d}-{_MONTHS[day.month - 1]}-{day.year}"


def _quote(folder: str) -> str:
    return '"' + folder.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _fetched_bytes(data: list[Any]) -> bytes | None:
    for part in data:
        if isinstance(part, tuple) and len(part) == 2 and isinstance(part[1], bytes):
            return part[1]
    return None


IMAPFactory = Callable[..., Any]


class ImapMailbox:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        folder: str,
        factory: IMAPFactory = imaplib.IMAP4_SSL,
        timeout: float = 30,
        writable: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._folder = folder
        self._factory = factory
        self._timeout = timeout
        # Seule la boîte des invités peut être vidée (docs/113) ; jamais celle de l'exploitant.
        self._writable = writable

    @classmethod
    def from_settings(cls, settings: Settings) -> "ImapMailbox":
        password = settings.imap_password.get_secret_value() if settings.imap_password else ""
        return cls(
            host=settings.imap_host,
            port=settings.imap_port,
            user=settings.imap_user,
            password=password,
            folder=settings.imap_folder,
        )

    @classmethod
    def guest_from_settings(cls, settings: Settings) -> "ImapMailbox":
        """La boîte des invités (docs/113), hébergée à part, vidée après chaque copie."""
        password = (
            settings.guest_imap_password.get_secret_value() if settings.guest_imap_password else ""
        )
        return cls(
            host=settings.guest_imap_host,
            port=settings.guest_imap_port,
            user=settings.guest_imap_user,
            password=password,
            folder=settings.guest_imap_folder,
            writable=True,
        )

    @contextmanager
    def _session(self, *, write: bool = False) -> Iterator[Any]:
        try:
            conn = self._factory(self._host, self._port, timeout=self._timeout)
        except (TimeoutError, OSError, ssl.SSLError) as exc:
            raise MailboxError(
                "connection", f"connexion IMAP impossible ({type(exc).__name__})"
            ) from None
        try:
            try:
                conn.login(self._user, self._password)
            except imaplib.IMAP4.error:
                raise MailboxError(
                    "auth",
                    "authentification IMAP refusée : vérifier JOBBOT_IMAP_USER et le mot de passe "
                    "d'application",
                ) from None
            status, _ = conn.select(_quote(self._folder), readonly=not write)
            if status != "OK":
                raise MailboxError("other", f"dossier IMAP introuvable : {self._folder}")
            yield conn
        except imaplib.IMAP4.abort as exc:
            raise MailboxError(
                "connection", f"connexion IMAP interrompue ({type(exc).__name__})"
            ) from None
        except (OSError, ssl.SSLError) as exc:
            raise MailboxError(
                "connection", f"connexion IMAP interrompue ({type(exc).__name__})"
            ) from None
        finally:
            # Déconnexion au mieux : une erreur ici ne doit pas masquer la vraie.
            with suppress(Exception):
                conn.logout()

    def fetch_since(
        self,
        since: date,
        *,
        limit: int,
        skip_message_ids: Callable[[set[str]], set[str]],
        newest_first: bool = False,
    ) -> list[FetchedEmail]:
        """E-mails reçus depuis `since`, du plus ancien au plus récent, au plus `limit`.

        Avec `newest_first`, les plus récents d'abord (échantillons).

        `skip_message_ids` reçoit les Message-ID trouvés et renvoie ceux déjà connus,
        qui ne sont pas téléchargés.
        """
        with self._session() as conn:
            status, data = conn.uid("SEARCH", None, "SINCE", imap_date(since))
            if status != "OK":
                raise MailboxError("other", "recherche IMAP refusée")
            uids = sorted((int(u) for u in (data[0] or b"").split()), reverse=newest_first)

            headers: dict[int, str] = {}
            for uid in uids:
                status, part = conn.uid(
                    "FETCH", str(uid), "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"
                )
                raw = _fetched_bytes(part) if status == "OK" else None
                match = _MESSAGE_ID.search(raw or b"")
                if match:
                    headers[uid] = match.group(1).decode("ascii", "replace")
            known = skip_message_ids(set(headers.values()))

            emails: list[FetchedEmail] = []
            for uid in uids:
                if headers.get(uid) in known:
                    continue
                if len(emails) >= limit:
                    break
                status, part = conn.uid("FETCH", str(uid), "(BODY.PEEK[])")
                raw = _fetched_bytes(part) if status == "OK" else None
                if raw is not None:
                    emails.append(FetchedEmail(uid=uid, raw=raw))
            return emails

    def clean(self, *, known: Callable[[set[str]], set[str]], before: date) -> int:
        """Boîte des invités (docs/113) : supprime les e-mails déjà copiés dans jobA1 (leur
        Message-ID est connu) et ceux reçus avant `before` (sans compte). Renvoie le nombre."""
        if not self._writable:
            raise MailboxError("other", "cette boîte est en lecture seule")
        with self._session(write=True) as conn:
            status, data = conn.uid("SEARCH", None, "ALL")
            if status != "OK":
                raise MailboxError("other", "recherche IMAP refusée")
            uids = [int(u) for u in (data[0] or b"").split()]
            headers: dict[int, str] = {}
            for uid in uids:
                status, part = conn.uid(
                    "FETCH", str(uid), "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"
                )
                raw = _fetched_bytes(part) if status == "OK" else None
                match = _MESSAGE_ID.search(raw or b"")
                if match:
                    headers[uid] = match.group(1).decode("ascii", "replace")
            copied = known(set(headers.values()))
            status, data = conn.uid("SEARCH", None, "BEFORE", imap_date(before))
            old = {int(u) for u in (data[0] or b"").split()} if status == "OK" else set()
            doomed = sorted({uid for uid in uids if headers.get(uid) in copied} | old)
            for uid in doomed:
                conn.uid("STORE", str(uid), "+FLAGS.SILENT", "(\\Deleted)")
            if doomed:
                conn.expunge()
            return len(doomed)
