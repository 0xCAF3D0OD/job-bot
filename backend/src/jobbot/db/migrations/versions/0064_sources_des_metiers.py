"""Les sources des familles de métiers (docs/116 §4)

Revision ID: 0064
Revises: 0063
Create Date: 2026-10-21

Les sources du catalogue pour chaque famille de métiers (communication, commerce, bâtiment,
santé et social, finance et administration, logistique, restauration), créées une fois ici :
un invité ne crée pas de source (table de la plateforme), il s'y abonne.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0064"
down_revision: str | None = "0063"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FAMILIES = (
    "communication",
    "commerce",
    "batiment",
    "sante-social",
    "finance-admin",
    "logistique",
    "restauration",
)


def _entries() -> list[dict[str, object]]:
    # Le catalogue tel qu'il est au moment de la migration.
    from jobbot.news import catalog

    return [
        {
            "kind": s.kind,
            "name": s.name,
            "url": s.url,
            "feed_url": s.feed_url,
            "match": s.match,
            "country": s.country,
            "language": s.language,
            "labour_market": s.labour_market,
        }
        for s in catalog.load().sources
        if set(s.domains) & set(FAMILIES)
    ]


def upgrade() -> None:
    statement = sa.text(
        "INSERT INTO news_sources (kind, name, url, feed_url, match, country, language,"
        " labour_market) VALUES (:kind, :name, :url, :feed_url, :match, :country, :language,"
        " :labour_market) ON CONFLICT (feed_url) DO NOTHING"
    )
    for entry in _entries():
        op.execute(statement.bindparams(**entry))


def downgrade() -> None:
    feeds = [str(e["feed_url"]) for e in _entries()]
    op.execute(
        sa.text(
            "DELETE FROM news_sources WHERE feed_url = ANY(:feeds) AND NOT EXISTS"
            " (SELECT 1 FROM profile_sources p WHERE p.source_id = news_sources.id)"
        ).bindparams(feeds=feeds)
    )
