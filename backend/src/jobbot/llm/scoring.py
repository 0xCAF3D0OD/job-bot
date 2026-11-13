"""Construction de la demande de note, format imposé de la réponse et validation.

Docs/06 §2 : l'IA ne reçoit que les blocs de profil actifs et le texte de l'offre ; elle
n'a aucun outil ; sa réponse suit un schéma JSON imposé, puis elle est revalidée ici.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from html import escape
from importlib import resources
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

PROMPT_VERSION = "score-v8"
# score-v3 n'ajoute que le télétravail (docs/26), score-v4 les signes d'arnaque (docs/30),
# score-v5 la phrase « pourquoi » et le niveau (docs/121 §C) : une note plus ancienne reste
# valable, elle n'est pas refaite (« Renoter » la refait, sur demande). score-v6 : la phrase
# « pourquoi » en deux morceaux (ce qui colle, la cause de l'écart), mis dans l'ordre par la note.
# score-v7 (prompt du 10 novembre, PR 18) : la note devient la somme de cinq parts, chacune avec sa
# phrase (« Comment la note est calculée ») ; une note plus ancienne garde son chiffre, sans détail.
# score-v8 (lot du 11 novembre au soir, PR 45 et 47) : dans le même appel, l'IA cite les passages
# de l'annonce qui correspondent au profil ; seules les citations retrouvées dans l'annonce sont
# gardées (`verified_quotes`). Une note plus ancienne reste valable, sans surlignage.
COMPATIBLE_VERSIONS = (
    "score-v2",
    "score-v3",
    "score-v4",
    "score-v5",
    "score-v6",
    "score-v7",
    "score-v8",
)
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/score-v8.md").read_text("utf-8")
# Citations de l'annonce : 5 au plus, de 2 à 12 mots chacune (décision de Kevin, 11 novembre).
QUOTE_MAX = 5
QUOTE_WORDS = (2, 12)
# Les cinq parts de la note et leur maximum (total 100), dans l'ordre d'affichage.
PART_MAX: dict[str, int] = {
    "skills": 40,
    "experience": 20,
    "location": 15,
    "languages": 15,
    "terms": 10,
}
PART_TEXT = 200
TIP_ACTIONS = ["skills", "experience", "languages", "criteria"]
KEYWORD_LENGTH = 25
MAX_OFFER_CHARS = 12_000
MAX_TOKENS = 4_000


class Point(BaseModel):
    text: str = Field(max_length=300)
    chunk_ids: list[int] = Field(default_factory=list)


class AskKeyword(BaseModel):
    text: str
    # Exigence couverte par un bloc du profil ; None sans profil (docs/11 §3).
    covered: bool | None = None


class ScamSignal(BaseModel):
    reason: str = Field(max_length=200)
    excerpt: str = Field(default="", max_length=400)


class ScorePart(BaseModel):
    key: Literal["skills", "experience", "location", "languages", "terms"]
    points: int
    text: str = ""
    check: bool = False


class ScoreTip(BaseModel):
    text: str
    action: Literal["skills", "experience", "languages", "criteria"] | None = None


class ScoreOutput(BaseModel):
    summary_role: str = Field(max_length=400)
    summary_asks: str = Field(max_length=400)
    summary_offers: str = Field(max_length=400)
    score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[Point] = Field(default_factory=list, max_length=6)
    gaps: list[Point] = Field(default_factory=list, max_length=6)
    # Étiquettes des cartes (score-v2) ; recoupées à la réception.
    keywords_role: list[str] = Field(default_factory=list)
    keywords_asks: list[AskKeyword] = Field(default_factory=list)
    keywords_offers: list[str] = Field(default_factory=list)
    # Télétravail (score-v3, docs/26 §2) ; absent d'une réponse score-v2 (lot en cours).
    remote: Literal["onsite", "hybrid", "full", "unknown"] | None = None
    remote_days: int | None = Field(default=None, ge=1, le=5)
    remote_region: str | None = Field(default=None, max_length=60)
    remote_from_switzerland: bool | None = None
    # Signes d'arnaque (score-v4, docs/30 §2) ; absents d'une réponse plus ancienne.
    scam_signals: list[ScamSignal] = Field(default_factory=list)
    # Pourquoi cette note, et le niveau (score-v5, docs/121 §C.1-2).
    why: str | None = Field(default=None, max_length=300)
    # score-v6 : les deux morceaux de la phrase, que why_sentence met dans l'ordre selon la note.
    why_fit: str | None = Field(default=None, max_length=120)
    why_gap: str | None = Field(default=None, max_length=120)
    level: Literal["above", "below"] | None = None
    level_detail: str | None = Field(default=None, max_length=200)
    # score-v7 : les cinq parts de la note et l'action qui la ferait monter.
    parts: list[ScorePart] = Field(default_factory=list, max_length=10)
    tip: ScoreTip | None = None
    # score-v8 : les passages de l'annonce qui correspondent au profil. À la réception, il ne reste
    # que ceux retrouvés dans l'annonce, écrits comme dans l'annonce.
    quotes: list[str] = Field(default_factory=list)


# Schéma envoyé à l'API (sorties structurées) : seulement des types simples, les bornes
# sont vérifiées par ScoreOutput à la réception.
_POINT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "chunk_ids": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["text", "chunk_ids"],
    "additionalProperties": False,
}
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary_role": {"type": "string"},
        "summary_asks": {"type": "string"},
        "summary_offers": {"type": "string"},
        "score": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "strengths": {"type": "array", "items": _POINT_SCHEMA},
        "gaps": {"type": "array", "items": _POINT_SCHEMA},
        "keywords_role": {"type": "array", "items": {"type": "string"}},
        "keywords_asks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "covered": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                },
                "required": ["text", "covered"],
                "additionalProperties": False,
            },
        },
        "keywords_offers": {"type": "array", "items": {"type": "string"}},
        "remote": {"type": "string", "enum": ["onsite", "hybrid", "full", "unknown"]},
        "remote_days": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "remote_region": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "remote_from_switzerland": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
        "scam_signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"reason": {"type": "string"}, "excerpt": {"type": "string"}},
                "required": ["reason", "excerpt"],
                "additionalProperties": False,
            },
        },
        "why_fit": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "why_gap": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "level": {"anyOf": [{"type": "string", "enum": ["above", "below"]}, {"type": "null"}]},
        "level_detail": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "parts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": list(PART_MAX)},
                    "points": {"type": "integer"},
                    "text": {"type": "string"},
                    "check": {"type": "boolean"},
                },
                "required": ["key", "points", "text", "check"],
                "additionalProperties": False,
            },
        },
        "quotes": {"type": "array", "items": {"type": "string"}},
        "tip": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "action": {
                            "anyOf": [
                                {
                                    "type": "string",
                                    "enum": ["skills", "experience", "languages", "criteria"],
                                },
                                {"type": "null"},
                            ]
                        },
                    },
                    "required": ["text", "action"],
                    "additionalProperties": False,
                },
                {"type": "null"},
            ]
        },
    },
    "required": [
        "summary_role",
        "summary_asks",
        "summary_offers",
        "score",
        "strengths",
        "gaps",
        "keywords_role",
        "keywords_asks",
        "keywords_offers",
        "remote",
        "remote_days",
        "remote_region",
        "remote_from_switzerland",
        "scam_signals",
        "why_fit",
        "why_gap",
        "level",
        "level_detail",
        "parts",
        "tip",
        "quotes",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class ProfileChunkData:
    id: int
    kind: str
    title: str
    content: str


@dataclass(frozen=True)
class OfferData:
    id: int
    title: str
    company: str | None
    location: str | None
    rate: str | None
    employment_type: str | None
    text: str | None
    # Vrai si `text` n'est que l'extrait de l'alerte (pas le texte complet de l'annonce).
    partial: bool


def profile_block(chunks: list[ProfileChunkData]) -> str:
    """Bloc de profil, stable d'un appel à l'autre (mis en cache) : ordre fixe par id."""
    if not chunks:
        return "<profil>\n(aucun bloc de profil : ne donne pas de note)\n</profil>"
    parts = [
        f'<bloc id="{c.id}" type="{c.kind}" titre="{escape(c.title)}">\n{c.content}\n</bloc>'
        for c in sorted(chunks, key=lambda c: c.id)
    ]
    return "<profil>\n" + "\n".join(parts) + "\n</profil>"


def profile_hash(chunks: list[ProfileChunkData]) -> str:
    return hashlib.sha256(profile_block(chunks).encode()).hexdigest()[:16]


def offer_message(offer: OfferData) -> str:
    fields = {
        "titre": offer.title,
        "entreprise": offer.company,
        "lieu": offer.location,
        "taux": offer.rate,
        "type": offer.employment_type,
    }
    header = "\n".join(f"{k} : {v}" for k, v in fields.items() if v)
    text = (offer.text or "").strip()[:MAX_OFFER_CHARS] or "(aucun texte)"
    nature = "extrait de l'alerte seulement" if offer.partial else "texte complet de l'annonce"
    # Les balises de fin éventuellement présentes dans l'annonce sont neutralisées.
    text = text.replace("</offre>", "</ offre>")
    return f"<offre>\n{header}\n\n[{nature}]\n{text}\n</offre>"


def request_params(
    model: str, effort: str, chunks: list[ProfileChunkData], offer: OfferData
) -> dict[str, Any]:
    """Paramètres communs aux appels directs et aux lots."""
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": INSTRUCTIONS},
            # Consignes + profil : préfixe stable, mis en cache entre les offres.
            {"type": "text", "text": profile_block(chunks), "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [{"role": "user", "content": offer_message(offer)}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
    }


class InvalidScore(ValueError):
    pass


def _label(value: str) -> str:
    return " ".join(value.split()).rstrip(".")[:KEYWORD_LENGTH].strip()


def _keywords(values: list[str], limit: int) -> list[str]:
    """Étiquettes courtes, sans doublon ni point final, dans l'ordre de l'IA."""
    seen: dict[str, str] = {}
    for value in values:
        text = _label(value)
        if text and text.casefold() not in seen:
            seen[text.casefold()] = text
    return list(seen.values())[:limit]


def _asks(values: list[AskKeyword]) -> list[AskKeyword]:
    seen: dict[str, AskKeyword] = {}
    for value in values:
        text = _label(value.text)
        if text and text.casefold() not in seen:
            seen[text.casefold()] = AskKeyword(text=text, covered=value.covered)
    return list(seen.values())[:5]


def remote_fields(output: "ScoreOutput | RemoteOutput") -> dict[str, Any]:
    """Télétravail cohérent : jours seulement pour un poste partiel, région et accès depuis la
    Suisse seulement pour un poste entièrement à distance."""
    remote = output.remote
    full = remote == "full"
    region = " ".join((output.remote_region or "").split())[:60] if full else ""
    return {
        "remote": remote,
        "remote_days": output.remote_days if remote == "hybrid" else None,
        "remote_region": region or None,
        "remote_from_switzerland": output.remote_from_switzerland if full else None,
    }


class RemoteOutput(BaseModel):
    """Relecture du seul télétravail d'une offre déjà notée (remote-v1, docs/26 §2)."""

    remote: Literal["onsite", "hybrid", "full", "unknown"]
    remote_days: int | None = Field(default=None, ge=1, le=5)
    remote_region: str | None = Field(default=None, max_length=60)
    remote_from_switzerland: bool | None = None


WHY_MAX = 80
# Les mots de la note : la phrase s'affiche juste après, elle ne les répète pas.
_NOTE_WORD = re.compile(r"^\s*(très proche|proche|à creuser|loin)\s*[:,\u2013-]?\s*", re.IGNORECASE)


def _part(text: str | None) -> str:
    """Un morceau de la phrase : sans le mot de la note, sans point final, une majuscule."""
    if not text:
        return ""
    clean = _NOTE_WORD.sub("", " ".join(text.split())).strip(" .;,")
    return clean[:1].upper() + clean[1:]


def why_sentence(score: int | None, fit: str | None, gap: str | None) -> str | None:
    """La phrase « pourquoi », cohérente avec la note (décision de Kevin) : pour une note basse
    (À creuser, Loin), la cause principale d'abord, puis ce qui colle ; pour une bonne note, ce
    qui colle d'abord, jamais un point faible en tête. 80 caractères au plus : la seconde idée
    tombe si elle ne tient pas."""
    first, second = _part(fit), _part(gap)
    if score is not None and score < 70 and second:
        first, second = second, first
    if not first:
        first, second = second, ""
    if not first:
        return None
    whole = f"{first}. {second}." if second else f"{first}."
    if len(whole) <= WHY_MAX:
        return whole
    alone = f"{first}."
    return alone if len(alone) <= WHY_MAX else alone[: WHY_MAX - 1].rsplit(" ", 1)[0] + "."


def _clean(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else clean[: limit - 1].rsplit(" ", 1)[0] + "…"


def score_parts(output: ScoreOutput) -> tuple[list[ScorePart], int | None]:
    """Les cinq parts, une par critère, dans l'ordre de PART_MAX, bornées à leur maximum ; la note
    devient leur somme (PR 18 : les points affichés sont ceux qui font la note). Une réponse sans
    les cinq parts garde sa note, sans détail : rien n'est inventé pour combler."""
    found: dict[str, ScorePart] = {}
    for part in output.parts:
        found.setdefault(part.key, part)
    if output.score is None or set(found) != set(PART_MAX):
        return [], output.score
    parts = [
        ScorePart(
            key=key,
            points=min(max(found[key].points, 0), top),
            text=_clean(found[key].text, PART_TEXT),
            check=found[key].check,
        )
        for key, top in PART_MAX.items()
    ]
    return parts, sum(p.points for p in parts)


# Apostrophes courbes et accents utilisés comme apostrophes : équivalents à l'apostrophe droite.
_APOSTROPHES = "\u2019\u2018\u02bc`\u00b4"
_SPACES = "\u00a0\u202f\u2007\u2009\u200a\u2060"


def _normalized(text: str) -> tuple[str, list[int]]:
    """Le texte pour la comparaison, et pour chaque caractère sa place dans le texte d'origine :
    espaces, insécables et retours à la ligne réduits à une espace, casse ignorée, apostrophes
    droite et courbe équivalentes."""
    out: list[str] = []
    places: list[int] = []
    for place, char in enumerate(text):
        if char.isspace() or char in _SPACES:
            if out and out[-1] != " ":
                out.append(" ")
                places.append(place)
            continue
        low = "'" if char in _APOSTROPHES else char.lower()
        for piece in low:
            out.append(piece)
            places.append(place)
    if out and out[-1] == " ":
        out.pop()
        places.pop()
    return "".join(out), places


def verified_quotes(quotes: list[str], offer_text: str | None) -> list[str]:
    """Les citations de l'IA retrouvées dans l'annonce, écrites comme dans l'annonce (jamais le
    texte de l'IA). Une citation introuvable, trop courte ou trop longue est écartée, sans
    erreur."""
    source = (offer_text or "")[:MAX_OFFER_CHARS]
    haystack, places = _normalized(source)
    found: dict[str, str] = {}
    for quote in quotes:
        needle, _ = _normalized(quote)
        if not QUOTE_WORDS[0] <= len(needle.split()) <= QUOTE_WORDS[1]:
            continue
        at = haystack.find(needle)
        if at < 0 or needle in found:
            continue
        found[needle] = source[places[at] : places[at + len(needle) - 1] + 1]
        if len(found) == QUOTE_MAX:
            break
    return list(found.values())


def parse_output(
    text: str, chunks: list[ProfileChunkData], offer_text: str | None = None
) -> ScoreOutput:
    """Valide la réponse et retire ce qui n'est pas prouvé par un bloc actif, ni retrouvé dans
    l'annonce (citations)."""
    try:
        output = ScoreOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    parts, total = score_parts(output)
    tip = output.tip if parts and output.tip and output.tip.text.strip() else None
    output = output.model_copy(
        update={
            "parts": parts,
            "score": total,
            "tip": tip.model_copy(update={"text": _clean(tip.text, PART_TEXT)}) if tip else None,
            **remote_fields(output),
            "scam_signals": [
                ScamSignal(
                    reason=" ".join(s.reason.split())[:100],
                    excerpt=" ".join(s.excerpt.split())[:150],
                )
                for s in output.scam_signals
                if s.reason.strip()
            ][:3],
            "keywords_role": _keywords(output.keywords_role, 3),
            "keywords_asks": _asks(output.keywords_asks),
            "keywords_offers": _keywords(output.keywords_offers, 4),
            "quotes": verified_quotes(output.quotes, offer_text),
            # Une phrase, nettoyée ; le détail du niveau seulement avec un niveau.
            "why": why_sentence(total, output.why_fit, output.why_gap)
            if output.why_fit or output.why_gap
            else (" ".join(output.why.split())[:140] or None if output.why else None),
            "level_detail": (" ".join(output.level_detail.split())[:100] or None)
            if output.level and output.level_detail
            else None,
        }
    )
    valid = {c.id for c in chunks}
    if not valid:
        asks = [k.model_copy(update={"covered": None}) for k in output.keywords_asks]
        return output.model_copy(
            update={
                "score": None,
                "strengths": [],
                "gaps": [],
                "keywords_asks": asks,
                "why": None,
                "level": None,
                "level_detail": None,
                "parts": [],
                "tip": None,
                "quotes": [],
            }
        )

    strengths = []
    for point in output.strengths:
        ids = [i for i in point.chunk_ids if i in valid]
        if ids:  # un point fort sans bloc qui le prouve est retiré (docs/06 §2)
            strengths.append(point.model_copy(update={"chunk_ids": ids}))
    gaps = [
        point.model_copy(update={"chunk_ids": [i for i in point.chunk_ids if i in valid]})
        for point in output.gaps
    ]
    return output.model_copy(update={"strengths": strengths[:4], "gaps": gaps[:4]})
