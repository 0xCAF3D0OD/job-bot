"""Profils d'essai (docs/17) : profil principal, sources suivies par profil

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("occupation", sa.Text()),
        sa.Column("is_main", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("preferences", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("news_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Un seul profil principal.
    op.create_index(
        "profiles_one_main",
        "profiles",
        ["is_main"],
        unique=True,
        postgresql_where=sa.text("is_main"),
    )
    op.create_table(
        "profile_sources",
        sa.Column(
            "profile_id",
            sa.BigInteger(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "source_id",
            sa.BigInteger(),
            sa.ForeignKey("news_sources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # Les réglages et sources d'avant passent au profil principal.
    op.execute(
        """
        INSERT INTO profiles (name, is_main, preferences, news_seen_at)
        SELECT 'Profil principal', true,
               COALESCE((SELECT value FROM settings WHERE key = 'news_preferences'), '{}'::jsonb),
               (SELECT (value #>> '{}')::timestamptz FROM settings WHERE key = 'news_seen_at')
        """
    )
    op.execute(
        """
        INSERT INTO profile_sources (profile_id, source_id, active)
        SELECT (SELECT id FROM profiles WHERE is_main), id, active FROM news_sources
        """
    )
    op.execute("DELETE FROM settings WHERE key IN ('news_preferences', 'news_seen_at')")
    op.drop_column("news_sources", "active")


def downgrade() -> None:
    op.add_column(
        "news_sources",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute(
        """
        UPDATE news_sources s SET active = COALESCE(
            (SELECT ps.active FROM profile_sources ps JOIN profiles p ON p.id = ps.profile_id
             WHERE p.is_main AND ps.source_id = s.id), false)
        """
    )
    op.execute(
        """
        INSERT INTO settings (key, value)
        SELECT 'news_preferences', preferences FROM profiles WHERE is_main
        """
    )
    op.drop_table("profile_sources")
    op.drop_index("profiles_one_main", table_name="profiles")
    op.drop_table("profiles")
