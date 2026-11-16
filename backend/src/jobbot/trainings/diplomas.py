"""Diplômes demandés par une formation, et ceux de la personne (Kevin, 16.11.2026).

Une formation accepte une liste de diplômes (vide = sans diplôme) ; un seul suffit. Les diplômes
de la personne viennent de ses blocs de profil, sans IA : un bloc Formation qui cite un Bachelor,
un diplôme ES ou HES en soins infirmiers ou un « Diplôme d'État infirmier », ou une expérience
dont le titre dit « infirmier·ère ». « J'ai ce diplôme » s'ajoute dans les réglages du compte
(clé `training_diplomas`), exportés et effacés avec lui ; rien n'est envoyé ailleurs.
"""

import re
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import ChunkKind, ProfileChunk, Setting

Diploma = Literal["soins_infirmiers", "bachelor_hes_sante", "bachelor_hes_social"]
DIPLOMAS: tuple[Diploma, ...] = ("soins_infirmiers", "bachelor_hes_sante", "bachelor_hes_social")
SETTING_KEY = "training_diplomas"

# Sur le texte normalisé (minuscules, sans accents ni ponctuation).
_NURSING_TITLE = re.compile(
    r"\b(bachelor|diplome|titre|ecole superieure|es|hes)\b.*\bsoins infirmiers\b"
    r"|\bsoins infirmiers\b.*\b(bachelor|diplome|es|hes)\b"
    r"|\bdiplome d etat (d )?infirmier"
    r"|\binfirmier(e)? diplome(e)?\b"
)
# « Infirmière », « Infirmier·ère » (normalisé « infirmier ere »), « Infirmiers » ;
# pas « aide-infirmière ».
_NURSE_JOB = re.compile(r"(?<!aide )\binfirmier(e|s|es)?\b")
_HEALTH_FIELDS = (
    r"(soins infirmiers|physiotherapie|ergotherapie|sage femme|nutrition|dietetique"
    r"|technique en radiologie|radiologie medicale|osteopathie)"
)
_BACHELOR_HEALTH = re.compile(rf"\bbachelor\b.*\b{_HEALTH_FIELDS}\b")
_BACHELOR_SOCIAL = re.compile(
    r"\bbachelor\b.*\b(travail social|education sociale|service social|animation socioculturelle)\b"
)


def detect(chunks: list[tuple[str, str, str]]) -> set[Diploma]:
    """Diplômes repérés dans les blocs (genre, titre, contenu)."""
    found: set[Diploma] = set()
    for kind, title, content in chunks:
        if kind == ChunkKind.FORMATION:
            text = normalize_text(f"{title} {content}")
            if _NURSING_TITLE.search(text):
                found.add("soins_infirmiers")
            if _BACHELOR_HEALTH.search(text):
                found.add("bachelor_hes_sante")
            if _BACHELOR_SOCIAL.search(text):
                found.add("bachelor_hes_social")
        elif kind == ChunkKind.EXPERIENCE and _NURSE_JOB.search(normalize_text(title)):
            found.add("soins_infirmiers")
    return found


async def declared(session: AsyncSession) -> set[Diploma]:
    value = await session.scalar(select(Setting.value).where(Setting.key == SETTING_KEY))
    return {d for d in value if d in DIPLOMAS} if isinstance(value, list) else set()


async def of_account(session: AsyncSession) -> tuple[set[Diploma], set[Diploma]]:
    """(repérés dans le profil, déclarés avec « J'ai ce diplôme »)."""
    rows = (
        await session.execute(
            select(ProfileChunk.kind, ProfileChunk.title, ProfileChunk.content).where(
                ProfileChunk.active.is_(True),
                ProfileChunk.kind.in_([ChunkKind.FORMATION, ChunkKind.EXPERIENCE]),
            )
        )
    ).all()
    return detect([(k, t, c) for k, t, c in rows]), await declared(session)


def eligible(prerequisites: list[str], diplomas: set[Diploma]) -> bool:
    return not prerequisites or any(p in diplomas for p in prerequisites)
