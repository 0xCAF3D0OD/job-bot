"""Les métiers et leurs recherches (docs/122, validé le 2026-10-22) : à l'accueil et dans
l'assistant des alertes, le métier choisi propose 2 ou 3 recherches toutes faites (docs/121 §B).
Un métier absent : l'IA propose des recherches à partir du seul nom du métier (`suggest`).
"""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources

import anthropic
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import welcome
from jobbot.core.normalize import normalize_text
from jobbot.db.models import Setting
from jobbot.llm.client import Refused
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)


@dataclass(frozen=True)
class Trade:
    name: str
    family: str | None
    aliases: tuple[str, ...]
    searches: tuple[str, ...]


TRADES: tuple[Trade, ...] = (
    Trade(
        "Vendeur·se",
        "commerce",
        ("vente", "vendeuse", "conseiller de vente"),
        ("vendeur vendeuse", "conseiller de vente", "gestionnaire du commerce de détail"),
    ),
    Trade(
        "Caissier·ère",
        "commerce",
        ("caisse", "caissière"),
        ("caissier caissière", "employé de commerce de détail"),
    ),
    Trade(
        "Gérant·e de magasin",
        "commerce",
        ("gérant", "responsable de magasin", "store manager"),
        ("gérant de magasin", "responsable de magasin", "store manager"),
    ),
    Trade(
        "Conseiller·ère clientèle",
        "commerce",
        ("service client", "call center", "relation client"),
        ("conseiller clientèle", "service clients", "call center"),
    ),
    Trade(
        "Commercial·e",
        "commerce",
        ("représentant", "vente externe", "account manager"),
        ("commercial", "représentant", "key account manager"),
    ),
    Trade(
        "Acheteur·se",
        "commerce",
        ("achats", "approvisionnement"),
        ("acheteur", "achats"),
    ),
    Trade(
        "Logisticien·ne",
        "logistique",
        ("logistique", "magasinier", "préparateur de commandes"),
        ("logisticien", "magasinier", "préparateur de commandes"),
    ),
    Trade(
        "Cariste",
        "logistique",
        ("chariot élévateur",),
        ("cariste", "chariot élévateur"),
    ),
    Trade(
        "Chauffeur·se poids lourd",
        "logistique",
        ("chauffeur PL", "camion", "permis C"),
        ("chauffeur poids lourd", "chauffeur permis C"),
    ),
    Trade(
        "Chauffeur·se livreur·se",
        "logistique",
        ("livreur", "livraison", "permis B"),
        ("chauffeur livreur", "livreur"),
    ),
    Trade(
        "Employé·e de déménagement",
        "logistique",
        ("déménageur",),
        ("déménageur",),
    ),
    Trade(
        "Responsable logistique",
        "logistique",
        ("supply chain", "chef d'entrepôt"),
        ("responsable logistique", "supply chain", "chef d'entrepôt"),
    ),
    Trade(
        "Cuisinier·ère",
        "restauration",
        ("cuisine", "chef de partie", "commis de cuisine"),
        ("cuisinier", "chef de partie", "commis de cuisine"),
    ),
    Trade(
        "Serveur·se",
        "restauration",
        ("service", "sommelier", "chef de rang"),
        ("serveur serveuse", "chef de rang", "employé de service"),
    ),
    Trade(
        "Barman·aid",
        "restauration",
        ("bar", "barista"),
        ("barman", "barista"),
    ),
    Trade(
        "Plongeur·se",
        "restauration",
        ("plonge", "aide de cuisine"),
        ("plongeur", "aide de cuisine"),
    ),
    Trade(
        "Réceptionniste",
        "restauration",
        ("réception", "front office"),
        ("réceptionniste", "réception hôtel"),
    ),
    Trade(
        "Employé·e d'hôtellerie",
        "restauration",
        ("femme de chambre", "gouvernante", "intendance"),
        ("employé d'intendance", "femme de chambre", "gouvernante"),
    ),
    Trade(
        "Boulanger·ère-pâtissier·ère",
        "restauration",
        ("boulanger", "pâtissier", "confiseur"),
        ("boulanger", "pâtissier", "boulanger-pâtissier-confiseur"),
    ),
    Trade(
        "Boucher·ère",
        "restauration",
        ("boucherie", "charcutier"),
        ("boucher", "charcutier"),
    ),
    Trade(
        "Infirmier·ère",
        "sante-social",
        ("infirmière", "soins infirmiers"),
        ("infirmier infirmière", "infirmier HES"),
    ),
    Trade(
        "Assistant·e en soins et santé communautaire (ASSC)",
        "sante-social",
        ("ASSC", "soins"),
        ("ASSC", "assistant en soins et santé communautaire"),
    ),
    Trade(
        "Aide-soignant·e",
        "sante-social",
        ("aide soignante", "auxiliaire de santé", "CRS"),
        ("aide-soignant", "auxiliaire de santé CRS"),
    ),
    Trade(
        "Assistant·e médical·e",
        "sante-social",
        ("cabinet médical", "secrétaire médicale"),
        ("assistante médicale", "secrétaire médicale"),
    ),
    Trade(
        "Aide à domicile",
        "sante-social",
        ("soins à domicile", "aide familiale"),
        ("aide à domicile", "auxiliaire de vie"),
    ),
    Trade(
        "Assistant·e en pharmacie",
        "sante-social",
        ("pharmacie", "pharmacien"),
        ("assistant en pharmacie", "pharmacien"),
    ),
    Trade(
        "Physiothérapeute",
        "sante-social",
        ("physio", "ergothérapeute"),
        ("physiothérapeute", "ergothérapeute"),
    ),
    Trade(
        "Assistant·e dentaire",
        "sante-social",
        ("dentaire", "hygiéniste"),
        ("assistante dentaire", "hygiéniste dentaire"),
    ),
    Trade(
        "Éducateur·rice social·e",
        "sante-social",
        ("éducateur", "éducation sociale"),
        ("éducateur social", "éducateur spécialisé"),
    ),
    Trade(
        "Assistant·e socio-éducatif·ve (ASE)",
        "sante-social",
        ("ASE", "socio-éducatif"),
        ("ASE", "assistant socio-éducatif"),
    ),
    Trade(
        "Éducateur·rice de l'enfance",
        "sante-social",
        ("petite enfance", "crèche", "EDE"),
        ("éducatrice de l'enfance", "crèche", "petite enfance"),
    ),
    Trade(
        "Enseignant·e",
        "sante-social",
        ("professeur", "maître", "école"),
        ("enseignant", "professeur"),
    ),
    Trade(
        "Assistant·e social·e",
        "sante-social",
        ("travail social", "intervenant social"),
        ("assistant social", "travailleur social"),
    ),
    Trade(
        "Électricien·ne",
        "batiment",
        ("électricité", "monteur électricien"),
        ("électricien", "monteur électricien"),
    ),
    Trade(
        "Menuisier·ère",
        "batiment",
        ("menuiserie", "ébéniste", "charpentier"),
        ("menuisier", "ébéniste", "charpentier"),
    ),
    Trade(
        "Maçon·ne",
        "batiment",
        ("maçonnerie", "gros œuvre"),
        ("maçon", "contremaître maçon"),
    ),
    Trade(
        "Peintre en bâtiment",
        "batiment",
        ("peinture", "plâtrier"),
        ("peintre en bâtiment", "plâtrier peintre"),
    ),
    Trade(
        "Installateur·rice sanitaire",
        "batiment",
        ("sanitaire", "plombier", "chauffagiste"),
        ("installateur sanitaire", "chauffagiste", "plombier"),
    ),
    Trade(
        "Polymécanicien·ne",
        "batiment",
        ("mécanicien", "usinage", "CNC"),
        ("polymécanicien", "mécanicien CNC", "usineur"),
    ),
    Trade(
        "Mécanicien·ne automobile",
        "batiment",
        ("garage", "mécatronicien"),
        ("mécanicien automobile", "mécatronicien d'automobiles"),
    ),
    Trade(
        "Opérateur·rice de production",
        "batiment",
        ("production", "ouvrier", "horlogerie"),
        ("opérateur de production", "ouvrier de production", "horlogerie opérateur"),
    ),
    Trade(
        "Agent·e d'entretien",
        "batiment",
        ("nettoyage", "concierge", "intendant"),
        ("agent d'entretien", "nettoyage", "concierge"),
    ),
    Trade(
        "Dessinateur·rice en bâtiment",
        "batiment",
        ("dessinateur", "architecte", "projeteur"),
        ("dessinateur en bâtiment", "architecte", "projeteur"),
    ),
    Trade(
        "Employé·e de commerce",
        "finance-admin",
        ("employé de bureau", "administratif", "CFC commerce"),
        ("employé de commerce", "employé administratif", "assistant administratif"),
    ),
    Trade(
        "Secrétaire",
        "finance-admin",
        ("assistante de direction", "réception"),
        ("secrétaire", "assistante de direction"),
    ),
    Trade(
        "Comptable",
        "finance-admin",
        ("comptabilité", "aide-comptable", "fiduciaire"),
        ("comptable", "aide-comptable", "fiduciaire"),
    ),
    Trade(
        "Spécialiste RH",
        "finance-admin",
        ("ressources humaines", "gestionnaire RH", "recrutement"),
        ("ressources humaines", "gestionnaire RH", "recruteur"),
    ),
    Trade(
        "Gestionnaire de dossiers",
        "finance-admin",
        ("assurance", "sinistres", "gestionnaire"),
        ("gestionnaire de dossiers", "gestionnaire sinistres"),
    ),
    Trade(
        "Conseiller·ère bancaire",
        "finance-admin",
        ("banque", "conseiller clientèle banque"),
        ("conseiller bancaire", "gestionnaire de fortune"),
    ),
    Trade(
        "Juriste",
        "finance-admin",
        ("droit", "paralégal"),
        ("juriste", "paralégal"),
    ),
    Trade(
        "Chargé·e de communication",
        "communication",
        ("communicant", "communicante", "communication"),
        ("chargé de communication", "communication", "relations publiques"),
    ),
    Trade(
        "Spécialiste marketing",
        "communication",
        ("marketing", "marketing digital", "chef de produit"),
        ("marketing", "marketing digital", "chef de produit"),
    ),
    Trade(
        "Graphiste",
        "communication",
        ("graphisme", "designer graphique", "polygraphe"),
        ("graphiste", "polygraphe"),
    ),
    Trade(
        "Rédacteur·rice",
        "communication",
        ("rédaction", "journaliste", "community manager"),
        ("rédacteur", "community manager", "journaliste"),
    ),
    Trade(
        "Développeur·se",
        "informatique",
        ("développeur", "programmeur", "software engineer"),
        ("développeur", "software engineer"),
    ),
    Trade(
        "Ingénieur·e DevOps",
        "informatique",
        ("devops", "SRE", "platform engineer"),
        ("DevOps", "SRE", "platform engineer"),
    ),
    Trade(
        "Administrateur·rice système",
        "informatique",
        ("admin système", "informaticien", "ingénieur système"),
        ("administrateur système", "ingénieur système"),
    ),
    Trade(
        "Technicien·ne support",
        "informatique",
        ("support informatique", "helpdesk", "informaticien CFC"),
        ("support informatique", "helpdesk", "technicien informatique"),
    ),
    Trade(
        "Data analyst",
        "informatique",
        ("données", "data", "BI"),
        ("data analyst", "business intelligence"),
    ),
    Trade(
        "Chef·fe de projet informatique",
        "informatique",
        ("chef de projet", "product owner", "scrum"),
        ("chef de projet informatique", "product owner"),
    ),
    Trade(
        "Agent·e de sécurité",
        None,
        ("sécurité", "surveillance", "gardiennage"),
        ("agent de sécurité", "surveillance"),
    ),
    Trade(
        "Coiffeur·se",
        None,
        ("coiffure", "esthéticienne"),
        ("coiffeur coiffeuse", "esthéticienne"),
    ),
    Trade(
        "Jardinier·ère",
        None,
        ("paysagiste", "horticulteur"),
        ("paysagiste", "horticulteur"),
    ),
)


def _forms(name: str) -> list[str]:
    """« Employé·e de commerce » : « employe de commerce » (sans la finale « ·e »)."""
    return [normalize_text(re.sub(r"·\w+", "", name.split("(")[0]))]


def _fits(key: str, typed: str) -> bool:
    """Chaque mot de la clé commence le mot tapé à la même place (« employe de commerce »
    va à « employee de commerce ») ; un seul mot tapé peut aussi commencer la clé (« devo »)."""
    keys, words = key.split(), typed.split()
    if not keys or len(words) < len(keys):
        return len(words) == 1 and len(typed) >= 4 and key.startswith(typed)
    return all(word.startswith(k) for k, word in zip(keys, words, strict=False))


def match(trade: str) -> Trade | None:
    """Le métier de la liste qui correspond à ce que la personne a tapé (début des mots,
    sans accents ni majuscules), le plus précis d'abord ; None si aucun."""
    typed = " ".join(normalize_text(trade).replace("-", " ").split())
    if len(typed) < 3:
        return None
    best: tuple[int, Trade] | None = None
    for item in TRADES:
        for key in [*_forms(item.name), *(normalize_text(a) for a in item.aliases)]:
            key = " ".join(key.replace("-", " ").split())
            if key and _fits(key, typed) and (best is None or len(key) > best[0]):
                best = (len(key), item)
    return best[1] if best else None


# Un métier absent de la liste : l'IA propose des recherches à partir du seul nom du métier
# (rien de personnel, environ 0,001 $), une fois par métier, gardées dans un réglage.
AI_KEY = "trade_searches"
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 200
ESTIMATE_USD = Decimal("0.002")
PROMPT_VERSION = "trade-searches-v1"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/trade-searches-v1.md").read_text("utf-8")
)
_JSON = re.compile(r"\{.*\}", re.S)


def parse_searches(text: str) -> list[str]:
    found = _JSON.search(text)
    try:
        data = json.loads(found.group(0)) if found else {}
    except json.JSONDecodeError:
        return []
    raw = data.get("searches") if isinstance(data, dict) else None
    cleaned = [" ".join(str(v).split())[:40] for v in raw or [] if isinstance(v, str) and v.strip()]
    return list(dict.fromkeys(cleaned))[:3]


async def suggest_with_ai(runtime: Runtime, trade: str) -> list[str]:
    """Les recherches proposées par l'IA pour un métier hors liste ; [] sans IA ou au plafond."""
    settings = runtime.settings
    if not settings.llm_configured:
        return []
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        return []
    name = " ".join(trade.replace("<", " ").replace(">", " ").split())[:80]
    params = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": f"<metier>{name}</metier>"}],
    }
    try:
        raw = await scoring_service.make_client(settings).score(params)
    except (Refused, anthropic.APIConnectionError, anthropic.RateLimitError):
        return []
    except anthropic.APIStatusError as exc:
        log.warning("trade_searches_failed", problem=account_problem(exc) or exc.status_code)
        return []
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="alerts")
    return parse_searches(raw.text)


async def prepare(runtime: Runtime) -> None:
    """Avant de proposer les recherches : pour un métier hors liste, demander à l'IA, une fois."""
    async with runtime.sessionmaker() as session:
        trade = (await welcome.state(session)).get("trade")
        saved = await session.scalar(select(Setting.value).where(Setting.key == AI_KEY))
    if not isinstance(trade, str) or not trade.strip() or match(trade) is not None:
        return
    if isinstance(saved, dict) and saved.get("trade") == trade.strip():
        return
    searches = await suggest_with_ai(runtime, trade)
    value = {"trade": trade.strip(), "searches": searches}
    async with runtime.sessionmaker.begin() as session:
        statement = insert(Setting).values(key=AI_KEY, value=value)
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=["user_id", "key"], set_={"value": statement.excluded.value}
            )
        )


async def searches_for(session: AsyncSession) -> list[str]:
    """Les recherches du métier de l'accueil, puis les postes gardés depuis le CV (docs/121
    §A) ; [] sans métier (l'exploitant, un compte d'avant l'accueil) : « Mon domaine » suit."""
    value = await welcome.state(session)
    trade = value.get("trade")
    roles = [r for r in value.get("roles") or [] if isinstance(r, str)]
    terms: list[str] = []
    if isinstance(trade, str) and trade.strip():
        found = match(trade)
        if found is not None:
            terms = list(found.searches)
        else:
            saved = await session.scalar(select(Setting.value).where(Setting.key == AI_KEY))
            if isinstance(saved, dict) and saved.get("trade") == trade.strip():
                terms = [t for t in saved.get("searches") or [] if isinstance(t, str)]
            terms = terms or [trade.strip()]
    seen = {normalize_text(t) for t in terms}
    for role in roles:
        if normalize_text(role) not in seen:
            terms.append(role)
            seen.add(normalize_text(role))
    return terms[:4]
