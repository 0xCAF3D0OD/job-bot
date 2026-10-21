"""Les actualités du métier (docs/116 §4) : une famille de métiers, ses sources.

Le métier (le premier mot de « Mon domaine », mis par l'accueil) choisit une famille du
catalogue ; le profil suit ses sources. Pour la restauration, faute de flux romand vérifié,
une veille Google Actualités du catalogue (docs/16 §4.2). Une fois par métier : le profil
garde le métier déjà suivi.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import NewsSource, Profile
from jobbot.news import catalog
from jobbot.profiles.service import subscribe

# Débuts de mots (sans accents) → famille. Le premier qui correspond l'emporte : les mots
# précis d'abord (« magasinier » avant « magasin », « chauffeur » avant « chauffagiste »).
_FAMILIES: list[tuple[str, tuple[str, ...]]] = [
    (
        "logistique",
        (
            "magasinier",
            "logist",
            "chauffeur",
            "livreu",
            "cariste",
            "transport",
            "supply",
            "expedit",
        ),
    ),
    (
        "informatique",
        (
            "informat",
            "develop",
            "devops",
            "logiciel",
            "software",
            "reseau",
            "cloud",
            "data",
            "cyber",
            "web",
        ),
    ),
    (
        "communication",
        (
            "commun",
            "marketing",
            "relations publiques",
            "presse",
            "journal",
            "redact",
            "graphi",
            "media",
            "evenement",
            "publicit",
            "contenu",
        ),
    ),
    (
        "restauration",
        (
            "cuisin",
            "patiss",
            "boulang",
            "restaur",
            "serveu",
            "barman",
            "boucher",
            "chocolat",
            "confis",
            "traiteur",
            "hotel",
            "sommeli",
        ),
    ),
    (
        "batiment",
        (
            "menuis",
            "charpent",
            "macon",
            "electricien",
            "plombier",
            "peintre",
            "carrel",
            "chauffag",
            "archit",
            "chantier",
            "ebenist",
            "couvreur",
            "install",
            "construct",
            "genie civil",
        ),
    ),
    (
        "sante-social",
        (
            "infirm",
            "soign",
            "medic",
            "sante",
            "educat",
            "social",
            "pharmac",
            "physio",
            "ergoth",
            "aide a domicile",
            "assistante dentaire",
            "sage femme",
        ),
    ),
    (
        "finance-admin",
        (
            "compta",
            "financ",
            "fiduciaire",
            "administr",
            "secretair",
            "assurance",
            "banque",
            "bancaire",
            "ressources humaines",
            "gestionnaire",
            "employe de commerce",
            "employee de commerce",
        ),
    ),
    (
        "commerce",
        (
            "vend",
            "vente",
            "commerc",
            "caissi",
            "magasin",
            "achat",
            "retail",
            "conseiller client",
            "conseillere client",
        ),
    ),
]


def family_of(trade: str) -> str | None:
    """La famille d'un métier, d'après le début de ses mots ; None si aucune ne va."""
    text = f" {normalize_text(trade).replace('-', ' ')}"
    for family, stems in _FAMILIES:
        if any(f" {stem}" in text for stem in stems):
            return family
    return None


def family_feeds(family: str | None) -> set[str]:
    """Les flux du catalogue pour une famille."""
    if family is None:
        return set()
    return {s.feed_url for s in catalog.load().sources if family in s.domains}


async def follow_trade(session: AsyncSession, profile: Profile, trade: str) -> None:
    """Le profil suit les sources de la famille du métier (créées par la migration 0064 :
    un invité s'abonne, il ne crée pas de source)."""
    name = " ".join(trade.split())
    preferences = dict(profile.preferences or {})
    if not name or preferences.get("trade_followed") == name.lower():
        return
    feeds = family_feeds(family_of(name))
    if feeds:
        ids = await session.scalars(select(NewsSource.id).where(NewsSource.feed_url.in_(feeds)))
        for source_id in ids:
            await subscribe(session, profile.id, source_id)
    preferences["trade_followed"] = name.lower()
    profile.preferences = preferences
