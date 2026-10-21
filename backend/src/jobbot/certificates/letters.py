"""Les lettres autour des certificats (docs/87 §4, 0.69.1) : demander une correction, ou un
certificat intermédiaire. Tu les relis, puis tu les envoies toi-même ; rien ne part d'ici.

- **La correction** : l'IA, sur demande, rédige une lettre polie qui cite les passages à
  reformuler et propose une formulation. Elle reçoit le texte sans ton nom, tes coordonnées ni
  les personnes nommées ; la plateforme ajoute ta signature. Sans IA, un modèle simple.
- **Le certificat intermédiaire** : un modèle, sans IA.

Aucune menace ni article de loi : la lettre demande, poliment.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources

import anthropic

from jobbot.certificates import service
from jobbot.db.models import Document
from jobbot.letters.service import load_identity
from jobbot.llm.common import SONNET, call, check_budget, clean
from jobbot.runtime import Runtime

MODEL = SONNET
MAX_TOKENS = 900
ESTIMATE_USD = Decimal("0.02")
INSTRUCTIONS = (
    resources.files("jobbot.llm")
    .joinpath("prompts/certificate-correction-v1.md")
    .read_text("utf-8")
)

SUBJECTS = {
    "correction": {
        "fr": "Demande de correction de mon certificat de travail",
        "de": "Bitte um Berichtigung meines Arbeitszeugnisses",
    },
    "interim": {
        "fr": "Demande de certificat de travail intermédiaire",
        "de": "Bitte um ein Zwischenzeugnis",
    },
}
# Ce qu'on propose à la place d'un passage qui dessert, par catégorie de formule.
BETTER = {
    "fr": {
        "performance": "« toujours à notre entière satisfaction »",
        "effort": "une phrase qui dit que les tâches ont été accomplies, sans « s'efforcer »",
        "departure": "ne pas mentionner le motif du départ",
    },
    "de": {
        "performance": "« stets zu unserer vollen Zufriedenheit »",
        "effort": "eine Formulierung ohne « bemüht »",
        "departure": "den Austrittsgrund nicht zu erwähnen",
    },
}
TEMPLATES = {
    "correction": {
        "fr": (
            "Madame, Monsieur,\n\nJe vous remercie pour le certificat de travail que vous m'avez "
            "remis. En le relisant, je me permets de vous demander de bien vouloir revoir les "
            "points suivants :\n\n{points}\n\nCes modifications refléteraient mieux notre "
            "collaboration. Je vous remercie par avance et reste à votre disposition pour en "
            "parler.\n\nAvec mes meilleures salutations,"
        ),
        "de": (
            "Sehr geehrte Damen und Herren\n\nVielen Dank für das Arbeitszeugnis. Beim Lesen "
            "möchte ich Sie höflich bitten, folgende Punkte zu überprüfen:\n\n{points}\n\nDiese "
            "Anpassungen würden unsere Zusammenarbeit besser widerspiegeln. Für Ihre Rückmeldung "
            "danke ich Ihnen im Voraus.\n\nFreundliche Grüsse"
        ),
    },
    "interim": {
        "fr": (
            "Madame, Monsieur,\n\nJe vous saurais gré de bien vouloir m'établir un certificat "
            "de travail intermédiaire, qui décrive mes tâches et apprécie mon travail ainsi que "
            "mon comportement.\n\nJe vous remercie par avance et vous prie d'agréer, Madame, "
            "Monsieur, mes salutations distinguées,"
        ),
        "de": (
            "Sehr geehrte Damen und Herren\n\nIch bitte Sie freundlich, mir ein Zwischenzeugnis "
            "auszustellen, das meine Aufgaben beschreibt und meine Leistung sowie mein Verhalten "
            "beurteilt.\n\nBesten Dank im Voraus.\n\nFreundliche Grüsse"
        ),
    },
}
CLOSING_POINT = {
    "fr": "ajouter une formule de fin (remerciements et vœux pour la suite)",
    "de": "eine Schlussformel zu ergänzen (Dank und gute Wünsche)",
}


class LetterUnavailable(Exception):
    """Le document n'est pas un certificat, ou son texte est illisible."""


@dataclass(frozen=True)
class Letter:
    subject: str
    text: str
    # Faux : le modèle simple, sans IA (non configurée, plafond atteint, réponse refusée).
    ai: bool
    reason: str | None = None


def sign(text: str, name: str | None) -> str:
    return f"{text.rstrip()}\n\n{name or '[ton prénom et nom]'}"


def _points(reading: service.Reading, language: str) -> list[str]:
    points = []
    for passage in reading.passages:
        if passage.tone != "bad" and not (
            passage.category == "performance" and (passage.level or 4) <= 2
        ):
            continue
        better = BETTER[language].get(passage.category)
        if language == "de":
            points.append(f"« {passage.text} »" + (f" : {better}" if better else ""))
        else:
            points.append(
                f"« {passage.text} »" + (f" : je vous propose {better}" if better else "")
            )
    if any("formule de fin" in note.text for note in reading.notes):
        points.append(CLOSING_POINT[language])
    return points


async def interim(runtime: Runtime, language: str = "fr") -> Letter:
    language = language if language in ("fr", "de") else "fr"
    async with runtime.sessionmaker() as session:
        identity = await load_identity(session)
    return Letter(
        SUBJECTS["interim"][language],
        sign(TEMPLATES["interim"][language], identity.name),
        ai=False,
    )


async def correction(runtime: Runtime, document_id: int, *, use_ai: bool) -> Letter:
    async with runtime.sessionmaker() as session:
        document = await session.get(Document, document_id)
        if document is None or document.kind != service.CERTIFICATE:
            raise LetterUnavailable("ce document n'est pas marqué comme certificat")
        text = document.extracted_text or ""
        if not text.strip():
            raise LetterUnavailable("texte illisible : dépose une version PDF avec du texte")
        identity = await load_identity(session)
    reading = service.read(text)
    language = reading.language if reading.language in ("fr", "de") else "fr"
    subject = SUBJECTS["correction"][language]
    points = _points(reading, language) or [
        "« … » : je vous propose « … »" if language == "fr" else "« … » : « … »"
    ]

    def template(reason: str | None) -> Letter:
        body = TEMPLATES["correction"][language].format(points="\n".join(f"- {p}" for p in points))
        return Letter(subject, sign(body, identity.name), ai=False, reason=reason)

    if not use_ai:
        return template(None)
    try:
        rate = await check_budget(runtime, ESTIMATE_USD, LetterUnavailable)
    except LetterUnavailable as exc:
        return template(str(exc))
    names = [identity.name or "", *(identity.name or "").split()]
    content = (
        f"<langue>{'allemand' if language == 'de' else 'français'}</langue>\n"
        f"<points>\n{clean(chr(10).join(points))}\n</points>\n"
        f"<certificat>\n{clean(service.without_names(text, names, identity)[: service.MAX_TEXT])}\n"
        "</certificat>"
    )
    params = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
    }
    try:
        raw, _ = await call(
            runtime, params, rate, purpose="certificate_letter", error=LetterUnavailable
        )
    except LetterUnavailable as exc:
        return template(str(exc))
    except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APIStatusError):
        return template("IA momentanément indisponible")
    body = raw.text.strip().strip('"«» ').strip()
    if not body:
        return template("réponse vide de l'IA")
    return Letter(subject, sign(body, identity.name), ai=True)


def end_year(text: str) -> int | None:
    """La dernière année citée : la fin de l'emploi, pour classer les certificats."""
    years = [int(y) for y in re.findall(r"\b(19[5-9]\d|20\d\d)\b", text)]
    return max(years) if years else None
