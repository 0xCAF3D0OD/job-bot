"""Actualités : pays, langue, sources « marché de l'emploi », langue des contenus

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Sources de départ (0023) : pays, langue (aucune pour le SECO, qui mêle français et
# allemand : chaque contenu porte la sienne), marché de l'emploi.
YOUTUBE = "https://www.youtube.com/feeds/videos.xml?channel_id="
DEFAULTS = [
    ("https://www.newsd.admin.ch/newsd/feeds/rss?lang=fr&org-nr=703", "CH", None, True),
    ("https://www.rts.ch/info/economie/?format=rss/news", "CH", "fr", False),
    ("https://www.letemps.ch/economie.rss", "CH", "fr", False),
    (
        YOUTUBE + "UCdngmbVKX1Tgre699-XLlUA",
        "INT",
        "en",
        False,
    ),
    (
        YOUTUBE + "UCSWj8mqQCcrcBlXPi4ThRDQ",
        "INT",
        "en",
        False,
    ),
]


def upgrade() -> None:
    op.add_column("news_sources", sa.Column("country", sa.Text()))
    op.add_column("news_sources", sa.Column("language", sa.Text()))
    op.add_column(
        "news_sources",
        sa.Column("labour_market", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("news_items", sa.Column("language", sa.Text()))
    for feed_url, country, language, labour_market in DEFAULTS:
        op.execute(
            sa.text(
                "UPDATE news_sources SET country = :country, language = :language,"
                " labour_market = :labour_market WHERE feed_url = :feed_url"
            ).bindparams(
                country=country, language=language, labour_market=labour_market, feed_url=feed_url
            )
        )


def downgrade() -> None:
    op.drop_column("news_items", "language")
    op.drop_column("news_sources", "labour_market")
    op.drop_column("news_sources", "language")
    op.drop_column("news_sources", "country")
