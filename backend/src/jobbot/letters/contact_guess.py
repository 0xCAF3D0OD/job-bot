"""Les coordonnées repérées en tête d'un CV, sur le serveur et sans IA (test du 10 novembre).

L'en-tête des lettres a besoin du nom et de l'adresse ; personne ne les saisissait aux premiers
pas. On les propose à partir du CV, avec les mêmes motifs que llm/redact.py (ce qui ne part
jamais à l'IA) : la personne les vérifie avant tout enregistrement. Rien n'est envoyé ni
journalisé ici.
"""

from dataclasses import dataclass

from jobbot.llm.redact import EMAIL, HEAD_LINES, HEADINGS, LOCALITY, NAME_LINE, PHONE, STREET

# Les coordonnées sont en haut du CV : on ne cherche pas plus loin que ces lignes.
CONTACT_LINES = 15


@dataclass(frozen=True)
class ContactGuess:
    name: str | None = None
    street: str | None = None
    postcode: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None


def _clean(value: str) -> str:
    return " ".join(value.split()).strip(" ,;|·•-")[:200]


def guess_contact(text: str) -> ContactGuess:
    lines = [line.strip() for line in text.splitlines() if line.strip()][:CONTACT_LINES]
    head = "\n".join(lines)
    name = street = postcode = city = None
    for index, line in enumerate(lines):
        # Une ligne peut tout porter : « Rue du Test 1, 1003 Lausanne | 079 … ».
        for part in (p.strip() for p in line.replace("|", ",").replace("·", ",").split(",")):
            if not part:
                continue
            if street is None and STREET.match(part):
                street = _clean(part)
            elif postcode is None and LOCALITY.match(part):
                rest = part[2:] if part[:2].upper() == "CH" else part
                postcode, _, place = rest.lstrip("- ").partition(" ")
                city = _clean(place) or None
        if (
            name is None
            and index < HEAD_LINES
            and NAME_LINE.match(line)
            and not HEADINGS.match(line)
        ):
            name = _clean(line)
    # Dans le doute, on laisse vide (Kevin, 16.11) : un champ vide vaut mieux qu'un champ faux
    # qu'on ne relit pas. Le NPA n'est repris qu'avec ses quatre chiffres suivis d'une localité ;
    # le téléphone et l'e-mail seulement s'il n'y en a qu'un en tête du CV.
    if not (postcode and len(postcode) == 4 and postcode.isdigit() and city):
        postcode = city = None
    phones = {_digits(m.group(0)) for m in PHONE.finditer(head)}
    emails = {m.group(0).lower() for m in EMAIL.finditer(head)}
    phone = PHONE.search(head) if len(phones) == 1 else None
    email = EMAIL.search(head) if len(emails) == 1 else None
    return ContactGuess(
        name=name,
        street=street,
        postcode=postcode,
        city=city,
        phone=_clean(phone.group(0)) if phone else None,
        email=email.group(0) if email else None,
    )


def _digits(phone: str) -> str:
    """Le même numéro écrit deux fois (« 079 … » et « +41 79 … ») ne compte qu'une fois."""
    digits = "".join(c for c in phone if c.isdigit())
    return digits[-9:]
