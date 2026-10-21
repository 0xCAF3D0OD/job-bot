"""Les codes de vérification des sites (docs/112).

Quand un invité crée son alerte, le site lui envoie un code à son adresse jobA1 (« Entrez
votre code de vérification »). Le code arrive dans la boîte de la plateforme : jobA1 le
reconnaît et le montre au compte, le temps de le recopier.

Un code : 4 à 8 chiffres (parfois en deux groupes, « 482 913 »), près d'un mot qui dit
« code » ou « vérification ». Un numéro de téléphone, une date, une année ou un prix n'en
sont pas.
"""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from jobbot.mail.message import ParsedEmail

# Français, allemand, anglais, italien.
WORDS = re.compile(
    r"code|vérification|verification|vérifier|verify|bestätigung|bestaetigung|"
    r"sicherheitscode|einmal|codice|verifica|one[- ]time|otp|pin\b",
    re.I,
)
# Un groupe de 4 à 8 chiffres, ou deux groupes de 3 (« 482 913 », « 482-913 »).
CANDIDATE = re.compile(
    r"(?<![\d.,:/+])(\d{3}[ \u00a0-]\d{3}|\d{4,8})"
    # Pas la suite d'un nombre (« 12.50 », « 3/4 »), ni un pourcentage ou un prix.
    r"(?![\d:/]|[.,]\d|\s?(?:%|chf|fr\.|€|\$))",
    re.I,
)
# Ce qui précède un numéro de téléphone, un prix ou une date.
NOT_A_CODE = re.compile(
    r"(\+\d{2}|tél|tel\.|phone|telefon|chf|fr\.|€|\$|n°|no\.|nr\.|ref|postal|npa|plz|case)[\s:.]*$",
    re.I,
)
# Le code est en général juste après le mot : on ne cherche pas plus loin.
WINDOW = 160


@dataclass(frozen=True)
class FoundCode:
    code: str


def _text(email: ParsedEmail) -> str:
    """Le sujet, le texte et le HTML : le code n'est parfois que dans l'un des deux."""
    html = BeautifulSoup(email.html, "html.parser").get_text(" ") if email.html else ""
    return " ".join(f"{email.subject or ''} \n {email.text or ''} \n {html}".split())


def _year(value: str) -> bool:
    return len(value) == 4 and value[:2] in ("19", "20")


def find_code(email: ParsedEmail) -> FoundCode | None:
    """Le code de vérification de l'e-mail, s'il en porte un."""
    text = _text(email)
    words = [m.end() for m in WORDS.finditer(text)]
    if not words:
        return None
    best: tuple[int, str] | None = None
    for match in CANDIDATE.finditer(text):
        value = re.sub(r"\D", "", match.group(1))
        before = text[max(0, match.start() - 12) : match.start()]
        if NOT_A_CODE.search(before) or _year(value):
            continue
        # Un morceau d'un plus long numéro (« 079 123 45 67 ») : pas un code.
        after = text[match.end() : match.end() + 4]
        if re.match(r"\s\d{2}\b", after):
            continue
        distances = [match.start() - end for end in words if 0 <= match.start() - end <= WINDOW]
        if not distances:
            continue
        distance = min(distances)
        if best is None or distance < best[0]:
            best = (distance, value)
    return FoundCode(best[1]) if best else None


def spaced(code: str) -> str:
    """« 482913 » se lit « 482 913 »."""
    return f"{code[:3]} {code[3:]}" if len(code) == 6 else code
