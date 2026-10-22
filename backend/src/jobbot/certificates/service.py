"""Lire un certificat de travail (docs/87).

1. **Sans IA** : les formules connues (`formulas.py`) donnent les passages, la note et le
   conseil. Gratuit, immédiat, toujours fait.
2. **Avec l'IA, sur demande** : une lecture détaillée, construite à partir du texte du
   certificat **sans** ton nom, tes coordonnées ni les noms des personnes, et des passages déjà
   repérés.

Ce qu'on garde : la lecture dans `certificate_readings`. Le document n'est jamais modifié.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.certificates import formulas
from jobbot.db.models import CertificateReading, Document
from jobbot.letters.service import load_identity
from jobbot.llm.common import SONNET, call, check_budget, clean, parse_reponse
from jobbot.llm.proposals import scrub
from jobbot.runtime import Runtime

Advice = Literal["attach", "on_request", "correct"]
CERTIFICATE = "certificate"
GRADES = {4: "très bon", 3: "bon", 2: "suffisant", 1: "à revoir"}
ADVICE = {
    "attach": "à joindre",
    "on_request": "à joindre si on le demande",
    "correct": "à faire corriger d'abord",
}
MODEL = SONNET
MAX_TOKENS = 1_500
ESTIMATE_USD = Decimal("0.04")
MAX_TEXT = 12_000
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/certificate-v1.md").read_text("utf-8")
)
# Une personne nommée après un titre : « M. Dupont », « Madame Anne Exemple », « Herr Meier ».
_TITLED = re.compile(
    r"\b(?:M\.|MM\.|Mme|Mmes|Mlle|Madame|Monsieur|Herr|Herrn|Frau|Dr\.?|Prof\.?)\s+"
    r"(?:[A-ZÀ-ÖØ-Ý][\w'\u2019-]+(?:\s+|$)){1,3}",
)
# Le bloc de signature : une ligne de deux ou trois mots capitalisés, vers la fin.
_SIGNATURE = re.compile(r"^\s*(?:[A-ZÀ-ÖØ-Ý][\w'\u2019-]+\s+){1,2}[A-ZÀ-ÖØ-Ý][\w'\u2019-]+\s*$")
SIGNATURE_LINES = 10


class ReadingUnavailable(Exception):
    """Pas un certificat lisible, pas d'IA, plafond atteint, ou réponse refusée."""


@dataclass
class Passage:
    text: str
    meaning: str
    tone: str
    category: str
    level: int | None = None


@dataclass
class Note:
    text: str
    tone: str


@dataclass
class Reading:
    language: str | None
    grade: int | None
    advice: Advice
    passages: list[Passage] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


def _language(text: str) -> str | None:
    lowered = text.casefold()
    german = sum(lowered.count(w) for w in (" und ", " die ", " der ", " wir ", "zufriedenheit"))
    french = sum(lowered.count(w) for w in (" et ", " les ", " nous ", " de ", "satisfaction"))
    if not german and not french:
        return None
    return "de" if german > french else "fr"


def read(text: str) -> Reading:
    """La lecture sans IA : les formules connues, la note, ce qui manque, le conseil."""
    language = _language(text)
    passages: list[Passage] = []
    taken: list[tuple[int, int]] = []
    for formula in formulas.FORMULAS:
        for match in formula.pattern.finditer(text):
            start, end = match.span()
            if any(start < e and s < end for s, e in taken):
                continue
            taken.append((start, end))
            passages.append(
                Passage(
                    " ".join(match.group(0).split()),
                    formula.meaning,
                    formula.tone,
                    formula.category,
                    formula.level,
                )
            )
    levels = [p.level for p in passages if p.level is not None]
    grade = min(levels) if levels else None
    notes: list[Note] = []
    if grade is None:
        notes.append(
            Note(
                "Aucune formule de prestation connue : un certificat sans appréciation du "
                "travail est en soi un signal.",
                "neutral",
            )
        )
    if language in formulas.CLOSING:
        missing = [
            formulas.CLOSING_NAMES[key]
            for key, pattern in formulas.CLOSING[language].items()
            if not pattern.search(text)
        ]
        if len(missing) == len(formulas.CLOSING_NAMES):
            notes.append(
                Note("Pas de formule de fin : ni regrets, ni remerciements, ni vœux.", "bad")
            )
        elif missing:
            notes.append(
                Note(f"La formule de fin ne contient pas {' ni '.join(missing)}.", "neutral")
            )
        sentence, superiors, colleagues = formulas.BEHAVIOUR[language]
        found = sentence.search(text)
        if found:
            part = found.group(0)
            boss, peers = superiors.search(part), colleagues.search(part)
            if boss and peers and peers.start() < boss.start():
                notes.append(
                    Note(
                        "Comportement : les collègues sont cités avant les supérieurs, un ordre "
                        "souvent lu comme une difficulté avec la hiérarchie.",
                        "bad",
                    )
                )
        else:
            notes.append(Note("Rien sur le comportement : un oubli qui se remarque.", "neutral"))
    bad = any(p.tone == "bad" for p in passages) or any(n.tone == "bad" for n in notes)
    advice: Advice
    if grade == 1 or any(p.category == "departure" and p.tone == "bad" for p in passages):
        advice = "correct"
    elif grade == 4 or (grade == 3 and not bad):
        advice = "attach"
    else:
        advice = "on_request"
    return Reading(language, grade, advice, passages, notes)


def explain(reading: Reading) -> str:
    """Une phrase qui dit la note et pourquoi."""
    if reading.grade is None:
        return "Pas de formule de prestation reconnue : lis-le avec « Lire en détail »."
    best = next(p for p in reading.passages if p.level == reading.grade)
    return f"Formule clé : « {best.text} ». {best.meaning}"


def without_names(text: str, names: list[str], identity: object | None = None) -> str:
    """Le texte pour l'IA : sans coordonnées, sans ton nom, sans les personnes nommées."""
    text = scrub(text, identity)
    for name in sorted({n for n in names if n and len(n) > 2}, key=len, reverse=True):
        text = re.sub(re.escape(name), "[la personne]", text, flags=re.IGNORECASE)
    text = _TITLED.sub("[nom retiré] ", text)
    lines = text.splitlines()
    tail = max(0, len(lines) - SIGNATURE_LINES)
    return "\n".join(
        "[nom retiré]" if i >= tail and _SIGNATURE.match(line) else line
        for i, line in enumerate(lines)
    )


async def save(session: AsyncSession, document: Document) -> CertificateReading:
    reading = read(document.extracted_text or "")
    found = await session.scalar(
        select(CertificateReading).where(CertificateReading.document_id == document.id)
    )
    if found is None:
        found = CertificateReading(document_id=document.id)
        session.add(found)
    found.language = reading.language
    found.grade = reading.grade
    found.advice = reading.advice
    found.passages = [asdict(p) for p in reading.passages]
    found.notes = [asdict(n) for n in reading.notes]
    found.rules_version = formulas.VERSION
    await session.flush()
    return found


def _identity_names(name: str | None) -> list[str]:
    parts = (name or "").split()
    return [name or "", *parts]


async def read_with_ai(runtime: Runtime, document_id: int) -> None:
    """La lecture détaillée : la note expliquée, ce qui manque, l'ordre, le conseil."""
    rate = await check_budget(runtime, ESTIMATE_USD, ReadingUnavailable)
    async with runtime.sessionmaker() as session:
        document = await session.get(Document, document_id)
        if document is None or document.kind != CERTIFICATE:
            raise ReadingUnavailable("ce document n'est pas marqué comme certificat")
        if not (document.extracted_text or "").strip():
            raise ReadingUnavailable("texte illisible : dépose une version PDF avec du texte")
        identity = await load_identity(session)
        text = without_names(document.extracted_text, _identity_names(identity.name), identity)
    reading = read(document.extracted_text)
    found = "\n".join(f"- « {clean(p.text)} » : {p.meaning}" for p in reading.passages)
    content = (
        f"<langue>{reading.language or 'inconnue'}</langue>\n"
        f"<reperes>\n{found or '- aucune formule connue'}\n</reperes>\n"
        f"<certificat>\n{clean(text[:MAX_TEXT])}\n</certificat>"
    )
    params = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
    }
    raw, _ = await call(runtime, params, rate, purpose="certificate", error=ReadingUnavailable)
    data = parse_reponse(raw.text)
    if data is None:
        raise ReadingUnavailable("réponse de l'IA illisible : réessaie plus tard")
    ai = _ai(data)
    async with runtime.sessionmaker.begin() as session:
        document = await session.get(Document, document_id)
        if document is None:
            return
        stored = await save(session, document)
        stored.ai = ai
        stored.ai_at = datetime.now(UTC)
        stored.advice = ai["advice"]


def _ai(data: dict[str, Any]) -> dict[str, Any]:
    advice = {"joindre": "attach", "si_demande": "on_request", "corriger": "correct"}
    grade = data.get("note")
    return {
        "grade": grade if isinstance(grade, int) and 1 <= grade <= 4 else None,
        "explanation": str(data.get("explication") or "").strip()[:1200],
        "missing": [str(m).strip()[:300] for m in data.get("manques") or [] if str(m).strip()][:6],
        "order": (str(data["ordre"]).strip()[:600] or None) if data.get("ordre") else None,
        "advice": advice.get(str(data.get("conseil")), "on_request"),
        "advice_text": str(data.get("conseil_texte") or "").strip()[:600],
    }
