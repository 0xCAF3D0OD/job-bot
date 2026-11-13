"""Rattrapage des offres jamais notées d'avant la version A2 (13 novembre), sur demande.

La migration 0085 a mis ces offres de côté (`score_final = 'a_rattraper'`) : la tâche des 10
minutes ne les reprend pas d'elle-même. `jobbot rattraper-notes` les compte par compte, avec le
coût estimé ; `--lancer` les rend à la tâche, qui les note (3 essais au plus) ou, sans texte, les
passe en « Note impossible » sans appel. Les offres d'alerte écartées restent sans note.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import bindparam, text

from jobbot.runtime import Runtime
from jobbot.scoring.service import ESTIMATE_USD, FINAL_BACKLOG, MANUAL_SOURCE, SET_ASIDE

# Le taux par défaut des Réglages (usd_chf_rate) : une estimation, pas une facture.
USD_CHF = Decimal("0.8")

_ELIGIBLE = """
    FROM evaluations e
    JOIN offers o ON o.id = e.offer_id AND o.user_id = e.user_id
   WHERE e.score_final = :backlog
     AND (o.status NOT IN :set_aside
          OR EXISTS (SELECT 1 FROM offer_links l
                      WHERE l.offer_id = o.id AND l.source = :manual))
"""


@dataclass(frozen=True)
class Backlog:
    account: int
    offers: int
    # Sans aucun texte : pas d'appel, « Note impossible » directe.
    without_text: int

    @property
    def cost_chf(self) -> Decimal:
        return ((self.offers - self.without_text) * ESTIMATE_USD * USD_CHF).quantize(
            Decimal("0.01")
        )


def _params() -> dict[str, object]:
    return {
        "backlog": FINAL_BACKLOG,
        "set_aside": tuple(str(s) for s in SET_ASIDE),
        "manual": MANUAL_SOURCE,
    }


async def count(runtime: Runtime) -> list[Backlog]:
    """Les offres à rattraper, par compte (accès propriétaire : tous les comptes)."""
    query = text(
        "SELECT e.user_id, count(*), count(*) FILTER (WHERE coalesce(btrim(o.description), '') = ''"
        " AND coalesce(btrim(o.snippet), '') = '')" + _ELIGIBLE + " GROUP BY e.user_id"
        " ORDER BY e.user_id"
    ).bindparams(bindparam("set_aside", expanding=True))
    async with runtime.sessionmaker() as session:
        rows = (await session.execute(query, _params())).all()
    return [Backlog(account=int(r[0]), offers=int(r[1]), without_text=int(r[2])) for r in rows]


async def release(runtime: Runtime, account: int | None = None) -> int:
    """Rend les offres à la tâche des 10 minutes ; renvoie leur nombre."""
    where = "" if account is None else " AND e.user_id = :account"
    query = text(
        "UPDATE evaluations SET score_final = NULL WHERE id IN (SELECT e.id"
        + _ELIGIBLE
        + where
        + ")"
    ).bindparams(bindparam("set_aside", expanding=True))
    params = _params() | ({} if account is None else {"account": account})
    async with runtime.sessionmaker.begin() as session:
        result = await session.execute(query, params)
    return int(getattr(result, "rowcount", 0) or 0)
