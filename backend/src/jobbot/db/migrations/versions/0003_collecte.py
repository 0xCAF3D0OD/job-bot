"""Collecte : searches, offers, offer_links, offer_sightings

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCES = "'jobup', 'indeed', 'jobroom', 'unknown'"
OFFER_STATUSES = "'new', 'filtered_out', 'to_review', 'later', 'ignored', 'preparing', 'applied'"


def upgrade() -> None:
    op.create_table(
        "searches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("message_id", sa.Text(), nullable=False, unique=True),
        sa.Column("imap_uid", sa.BigInteger()),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject", sa.Text()),
        sa.Column("alert_label", sa.Text()),
        sa.Column("raw_key", sa.Text(), nullable=False),
        sa.Column("parse_status", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.Text()),
        sa.Column("error", sa.Text()),
        sa.Column("results_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_offers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "job_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_runs.run_id", ondelete="SET NULL"),
        ),
        sa.CheckConstraint(f"source IN ({SOURCES})", name="searches_source_check"),
        sa.CheckConstraint(
            "parse_status IN ('parsed', 'empty', 'unrecognized', 'failed')",
            name="searches_parse_status_check",
        ),
    )
    op.create_index("ix_searches_received_at", "searches", ["received_at"])

    op.create_table(
        "offers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("fingerprint", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("rate_min", sa.Integer()),
        sa.Column("rate_max", sa.Integer()),
        sa.Column("snippet", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(f"status IN ({OFFER_STATUSES})", name="offers_status_check"),
    )
    op.create_index("ix_offers_first_seen_at", "offers", ["first_seen_at"])

    op.create_table(
        "offer_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text()),
        sa.Column("url", sa.Text(), nullable=False),
        sa.UniqueConstraint("offer_id", "source"),
        sa.CheckConstraint(f"source IN ({SOURCES})", name="offer_links_source_check"),
    )
    op.create_index(
        "uq_offer_links_source_external_id",
        "offer_links",
        ["source", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )

    op.create_table(
        "offer_sightings",
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "search_id",
            sa.BigInteger(),
            sa.ForeignKey("searches.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        # Vrai si l'offre est apparue pour la première fois dans cette alerte.
        sa.Column("is_first", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_offer_sightings_search_id", "offer_sightings", ["search_id"])


def downgrade() -> None:
    op.drop_table("offer_sightings")
    op.drop_table("offer_links")
    op.drop_table("offers")
    op.drop_table("searches")
