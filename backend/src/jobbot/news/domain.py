"""« Mon domaine » (docs/16 §2) : mots-clés qui filtrent les actualités, sans IA.

La comparaison ignore majuscules, accents et ponctuation, et se fait mot à mot :
« CI/CD » trouve « ci-cd », « Kubernetes » ne trouve pas « Kubernetesque ».
"""

from collections import Counter

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Application, Evaluation, Setting

MAX_KEYWORDS = 30
PREFILL = 8


def matched(keywords: list[str], *texts: str | None) -> list[str]:
    """Mots-clés présents dans les textes, dans l'ordre de la liste."""
    haystack = f" {normalize_text(' '.join(t for t in texts if t))} "
    return [k for k in keywords if (needle := normalize_text(k)) and f" {needle} " in haystack]


async def suggest(session: AsyncSession) -> list[str]:
    """Mots-clés « Poste » les plus fréquents des offres postulées ou bien notées (≥ 70)."""
    applied = select(Application.offer_id)
    rows = await session.scalars(
        select(Evaluation.keywords_role).where(
            or_(Evaluation.offer_id.in_(applied), Evaluation.score >= 70)
        )
    )
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for keywords in rows:
        for keyword in keywords or []:
            if not isinstance(keyword, str) or not (key := normalize_text(keyword)):
                continue
            counts[key] += 1
            labels.setdefault(key, keyword.strip())
    return [labels[key] for key, _ in counts.most_common(PREFILL)]


PREFERENCES_KEY = "news_preferences"


async def _preferences(session: AsyncSession) -> dict[str, object]:
    value = await session.scalar(select(Setting.value).where(Setting.key == PREFERENCES_KEY))
    return value if isinstance(value, dict) else {}


async def keywords(session: AsyncSession) -> list[str]:
    """« Mon domaine » enregistré (Réglages → Actualités), sinon la suggestion du profil."""
    saved = (await _preferences(session)).get("domain_keywords")
    if isinstance(saved, list):
        return [k for k in saved if isinstance(k, str)]
    return await suggest(session)


async def languages(session: AsyncSession) -> list[str]:
    """Langues choisies dans les filtres des Actualités ; à défaut, français et anglais."""
    saved = (await _preferences(session)).get("languages")
    chosen = [k for k in saved if isinstance(k, str)] if isinstance(saved, list) else []
    return chosen or ["fr", "en"]
