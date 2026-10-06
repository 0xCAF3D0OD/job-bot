"""Actualités : sources (flux RSS, chaînes YouTube) et articles relevés

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCES = [
    # type, nom, adresse du site, flux, filtre (auteur, titre ou texte)
    (
        "articles",
        "SECO — marché du travail",
        "https://www.seco.admin.ch",
        "https://www.newsd.admin.ch/newsd/feeds/rss?lang=fr&org-nr=703",
        "Staatssekretariat für Wirtschaft",
    ),
    (
        "articles",
        "RTS Info — Économie",
        "https://www.rts.ch/info/economie/",
        "https://www.rts.ch/info/economie/?format=rss/news",
        None,
    ),
    (
        "articles",
        "Le Temps — Économie",
        "https://www.letemps.ch/economie",
        "https://www.letemps.ch/economie.rss",
        None,
    ),
    (
        "videos",
        "TechWorld with Nana",
        "https://www.youtube.com/@TechWorldwithNana",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCdngmbVKX1Tgre699-XLlUA",
        None,
    ),
    (
        "videos",
        "KodeKloud",
        "https://www.youtube.com/@KodeKloud",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCSWj8mqQCcrcBlXPi4ThRDQ",
        None,
    ),
]


def upgrade() -> None:
    sources = op.create_table(
        "news_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("feed_url", sa.Text(), nullable=False, unique=True),
        sa.Column("match", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("kind IN ('articles', 'videos')", name="news_sources_kind_check"),
    )
    op.create_table(
        "news_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_id",
            sa.BigInteger(),
            sa.ForeignKey("news_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("summary", sa.Text()),
        sa.Column("image_url", sa.Text()),
        sa.Column("image_key", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_news_items_published_at", "news_items", ["published_at"])
    op.bulk_insert(
        sources,
        [{"kind": k, "name": n, "url": u, "feed_url": f, "match": m} for k, n, u, f, m in SOURCES],
    )


def downgrade() -> None:
    op.drop_table("news_items")
    op.drop_table("news_sources")
