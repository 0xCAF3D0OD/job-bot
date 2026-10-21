"""Le métier du compte (docs/116 §3) : les mots de ses alertes et de son domaine.

Une recommandation d'un site (jobup « Suggestions d'offres ») n'est gardée que si son titre
partage un mot avec eux. La comparaison ignore majuscules, accents et ponctuation, et se fait
sur le début des mots (six lettres au plus) : « communicante » trouve « Chargé·e de
communication », « pâtissier » trouve « Pâtissier-confiseur » ; « menuisier » ne trouve rien.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import AlertSearch
from jobbot.news import domain

STEM = 6
MIN_WORD = 4
# Les mots trop généraux pour dire un métier.
_COMMON = {
    "pour",
    "avec",
    "dans",
    "chez",
    "des",
    "les",
    "une",
    "sans",
    "plus",
    "tout",
    "toute",
    "emploi",
    "poste",
    "postes",
    "travail",
    "stage",
    "stagiaire",
    "junior",
    "senior",
    "responsable",
    "assistant",
    "assistante",
    "collaborateur",
    "collaboratrice",
    "suisse",
    "lausanne",
    "geneve",
    "fribourg",
    "neuchatel",
    "valais",
    "vaud",
}


def _stems(text: str) -> set[str]:
    words = normalize_text(text).replace("-", " ").split()
    return {w[:STEM] for w in words if len(w) >= MIN_WORD and w not in _COMMON}


async def trade_stems(session: AsyncSession) -> set[str]:
    """Les débuts de mots du métier : alertes actives et domaine du profil principal."""
    terms = await session.scalars(select(AlertSearch.terms).where(AlertSearch.active))
    keywords = await domain.keywords(session)
    stems: set[str] = set()
    for text in [*terms, *keywords]:
        stems |= _stems(text)
    return stems


def on_topic(title: str, stems: set[str]) -> bool:
    """Le titre partage-t-il un mot avec le métier ? Sans mot connu, tout passe."""
    return not stems or bool(_stems(title) & stems)
