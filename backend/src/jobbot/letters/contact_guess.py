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
    email = EMAIL.search(head)
    phone = PHONE.search(head)
    return ContactGuess(
        name=name,
        street=street,
        postcode=postcode if postcode and len(postcode) == 4 and postcode.isdigit() else None,
        city=city if postcode else None,
        phone=_clean(phone.group(0)) if phone else None,
        email=email.group(0) if email else None,
    )
