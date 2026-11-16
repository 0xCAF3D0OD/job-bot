"""Les réponses d'employeurs transférées à la main (docs/146, accord de Kevin du 16.11.2026).

La personne transfère la réponse d'une entreprise (entretien, refus…) vers son adresse jobA1,
celle des alertes. Un transfert fait à la main n'a pas les en-têtes d'un filtre Gmail
(X-Forwarded-To/For) et porte, dans son corps, l'en-tête du message d'origine (« De : … »).

- Rattachement : l'expéditeur d'origine, comparé au lien et à l'e-mail de chaque candidature,
  puis le nom de l'entreprise dans le message.
- Classement : des mots-clés en français, allemand, anglais et italien ; aucun appel à l'IA.
- Rien ne change tout seul (I-3) : la candidature garde son statut ; une notification demande
  « entretien ? » ou « refus ? » et ouvre la candidature, où la personne choisit.

Données (docs/regles-securite-donnees.md) : ni le texte ni l'expéditeur ne sont gardés, seuls
le type de réponse et sa date, sur la candidature (exportés et effacés avec elle). L'e-mail
brut n'est jamais stocké (il reste « ignoré », comme tout expéditeur qui n'est aucun site) ;
les journaux ne disent que le type et si une candidature a été trouvée (J-1). La notification
ne contient que le nom de l'entreprise, déjà dans la candidature, jamais une coordonnée (X-5).
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from sqlalchemy import select

from jobbot.db.models import Application
from jobbot.log import get_logger
from jobbot.mail.message import ParsedEmail
from jobbot.notify import service as notify
from jobbot.runtime import Runtime

log = get_logger(__name__)

KIND = "employer_reply"
INTERVIEW, REFUSAL, OTHER = "entretien", "refus", "autre"
# Une candidature plus ancienne n'attend plus de réponse.
LOOK_BACK = timedelta(days=365)

# L'en-tête du message d'origine, tel que l'écrivent Gmail, Outlook, Apple Mail, Thunderbird :
# une ligne « De : » suivie de près d'une ligne « Date : », « Envoyé : », « Objet : »…
_FROM_LINE = re.compile(r"^[\s>*]*(from|de|von|da)\s*:\s*\**\s*(.+)$", re.IGNORECASE)
_NEXT_LINE = re.compile(
    r"^[\s>*]*(sent|date|datum|envoye|gesendet|inviato|subject|objet|betreff|oggetto|to|a|an)"
    r"\s*:",
    re.IGNORECASE,
)
_ADDRESS = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
_PREFIX = re.compile(r"^\s*((fwd?|tr|wg|rv|enc|i)\s*:\s*)+", re.IGNORECASE)

# Les domaines qui ne disent rien de l'employeur : boîtes personnelles, logiciels de
# recrutement qui écrivent au nom de l'entreprise, sites d'annonces. Le nom de l'entreprise
# dans le message décide alors.
GENERIC_DOMAINS = frozenset(
    {
        "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com",
        "icloud.com", "me.com", "bluewin.ch", "gmx.ch", "gmx.net", "gmx.de", "proton.me",
        "protonmail.com", "sunrise.ch", "hispeed.ch",
        "myworkday.com", "workday.com", "smartrecruiters.com", "successfactors.com",
        "successfactors.eu", "greenhouse.io", "lever.co", "personio.de", "personio.com",
        "recruitee.com", "teamtailor.com", "workable.com", "icims.com", "taleo.net",
        "softgarden.io", "softgarden.de", "umantis.com", "onlyfy.io", "prescreen.io",
        "join.com", "jobs.ch", "jobup.ch", "linkedin.com", "indeed.com", "arbeit.swiss",
    }
)  # fmt: skip
# Les formes juridiques, retirées du nom avant de le chercher.
LEGAL_FORMS = frozenset(
    {"sa", "ag", "sarl", "gmbh", "ltd", "llc", "inc", "sagl", "srl", "spa", "co", "kg", "plc"}
)

# Mots-clés, sans accents ni majuscules. Un refus parle souvent de l'entretien passé : il est
# cherché d'abord. Un accusé de réception promet parfois un entretien : il reste « autre ».
REFUSAL_WORDS = (
    "malheureusement", "nous regrettons", "au regret", "pas retenu", "pas ete retenu",
    "ne pas donner suite", "pas donner suite", "pas pu retenir", "autre candidat",
    "autres candidat", "leider", "absage", "nicht berucksichtigen", "nicht weiter verfolgen",
    "anderen kandidat", "unfortunately", "regret to inform", "not to proceed",
    "not be moving forward", "not moving forward", "other candidates", "not been successful",
    "purtroppo",
)  # fmt: skip
RECEIPT_WORDS = (
    "bien recu votre candidature", "bien recu ta candidature", "accuse reception",
    "accusons reception", "thank you for applying", "we have received your application",
    "eingang ihrer bewerbung", "ihre bewerbung ist bei uns eingegangen",
)  # fmt: skip
INTERVIEW_WORDS = (
    "entretien", "vous rencontrer", "te rencontrer", "rendez-vous", "vos disponibilites",
    "tes disponibilites", "echange telephonique", "visioconference", "vorstellungsgesprach",
    "gesprach", "kennenlernen", "interview", "your availability", "meet you",
    "schedule a call", "colloquio",
)  # fmt: skip


@dataclass(frozen=True)
class Forward:
    """Le message d'origine, lu dans le transfert : son domaine et son texte (en mémoire)."""

    sender_domain: str | None
    text: str


def plain(value: str) -> str:
    """Minuscules, sans accents, espaces simples : la forme où l'on cherche les mots."""
    value = value.replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(value.lower().split())


def base_domain(domain: str) -> str:
    """« jobs.ivypartners.ch » → « ivypartners.ch » ; « mail.firm.co.uk » → « firm.co.uk »."""
    labels = domain.lower().strip(".").split(".")
    keep = 3 if len(labels) >= 3 and labels[-2] in {"co", "com", "ac", "gov"} else 2
    return ".".join(labels[-keep:])


def _body_text(email: ParsedEmail) -> str:
    if email.text and email.text.strip():
        return email.text
    if email.html:
        return BeautifulSoup(email.html, "html.parser").get_text("\n")
    return ""


def read_forward(email: ParsedEmail) -> Forward | None:
    """Le message d'origine d'un transfert fait à la main, ou None si ce n'en est pas un."""
    if email.forwarded:  # transféré par un filtre : une alerte, ou un filtre trop large
        return None
    lines = _body_text(email).splitlines()
    for index, line in enumerate(lines):
        found = _FROM_LINE.match(plain(line))
        if found is None:
            continue
        following = [plain(other) for other in lines[index + 1 : index + 5] if other.strip()]
        if not any(_NEXT_LINE.match(other) for other in following):
            continue
        address = _ADDRESS.search(line)
        subject = _PREFIX.sub("", email.subject or "")
        text = "\n".join([subject, *lines[index:]])
        return Forward(address.group(1).lower() if address else None, text)
    return None


def classify(text: str) -> str:
    words = plain(text)
    if any(word in words for word in REFUSAL_WORDS):
        return REFUSAL
    if any(word in words for word in RECEIPT_WORDS):
        return OTHER
    if any(word in words for word in INTERVIEW_WORDS):
        return INTERVIEW
    return OTHER


def company_words(company: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", plain(company))
    return [word for word in words if word not in LEGAL_FORMS]


def _domains(application: Application) -> set[str]:
    found: set[str] = set()
    if application.contact_email and "@" in application.contact_email:
        found.add(base_domain(application.contact_email.rpartition("@")[2]))
    if application.application_url:
        url = application.application_url.strip()
        if "@" in url and "://" not in url:  # un e-mail utilisé comme moyen de candidature
            found.add(base_domain(url.rpartition("@")[2]))
        else:
            host = urlparse(url if "://" in url else f"https://{url}").hostname
            if host:
                found.add(base_domain(host))
    return found - GENERIC_DOMAINS


def _by_domain(application: Application, domain: str) -> bool:
    if domain in _domains(application):
        return True
    # « ivypartners.ch » et « Ivy Partners SA » : le nom collé est celui du domaine.
    joined = "".join(company_words(application.company))
    label = domain.split(".")[0]
    return len(joined) >= 4 and joined == label


def _by_name(application: Application, text: str) -> bool:
    words = company_words(application.company)
    if len("".join(words)) < 4:
        return False
    return re.search(rf"\b{re.escape(' '.join(words))}\b", text) is not None


def match(applications: list[Application], forward: Forward) -> Application | None:
    """La candidature de la réponse : par le domaine de l'expéditeur, sinon par le nom de
    l'entreprise. Plusieurs entreprises possibles : aucune (la personne choisit elle-même) ;
    plusieurs candidatures dans la même entreprise : la plus récente."""
    domain = base_domain(forward.sender_domain) if forward.sender_domain else None
    found: list[Application] = []
    if domain and domain not in GENERIC_DOMAINS:
        found = [a for a in applications if _by_domain(a, domain)]
    if not found:
        text = " ".join(re.findall(r"[a-z0-9]+", plain(forward.text)))
        found = [a for a in applications if _by_name(a, text)]
    if len({" ".join(company_words(a.company)) for a in found}) != 1:
        return None
    return max(found, key=lambda a: (a.sent_at, a.id))


def message(company: str | None, kind: str, click: str | None = None) -> notify.Message:
    if company is None:
        return notify.Message(
            title="Réponse d'entreprise reçue",
            message="La candidature n'a pas été retrouvée : mets-la à jour dans Candidatures.",
            tags=["envelope"],
            click=click,
        )
    title = {
        INTERVIEW: f"{company} t'a répondu : entretien ?",
        REFUSAL: f"{company} t'a répondu : refus ?",
    }.get(kind, f"{company} t'a répondu")
    return notify.Message(
        title=title,
        message="Ouvre la candidature pour la mettre à jour.",
        tags=["envelope"],
        click=click,
    )


async def handle(runtime: Runtime, email: ParsedEmail, today: date | None = None) -> bool:
    """Une réponse transférée, dans le compte en cours : rattachée, rangée, annoncée. False si
    l'e-mail n'est pas un transfert fait à la main."""
    forward = read_forward(email)
    if forward is None:
        return False
    kind = classify(forward.text)
    since = (today or email.received_at.date()) - LOOK_BACK
    async with runtime.sessionmaker.begin() as session:
        applications = list(
            await session.scalars(select(Application).where(Application.sent_at >= since))
        )
        found = match(applications, forward)
        if found is not None:
            found.reply_kind = kind
            found.reply_at = email.received_at
        company = found.company if found is not None else None
        application_id = found.id if found is not None else None
    link = "/candidatures/suivi"
    if application_id is not None:
        link += f"?candidature={application_id}"
    click = f"{runtime.settings.public_url.rstrip('/')}{link}"
    await notify.deliver(runtime, message(company, kind, click), kind=KIND, link=link)
    log.info("employer_reply", kind=kind, matched=application_id is not None)
    return True
