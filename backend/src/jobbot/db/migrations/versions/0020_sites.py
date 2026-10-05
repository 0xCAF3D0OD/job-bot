"""Sites suivis : intégrés (jobup, Indeed) et ajoutés (jobs.ch, LinkedIn…), lus par l'IA

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SLUG = "source ~ '^[a-z0-9]{2,30}$'"
SITES = [
    # slug, nom, expéditeurs, adresse, lecture, actif
    ("jobup", "jobup", ["jobup.ch"], "https://www.jobup.ch", "jobup", True),
    ("indeed", "Indeed", ["indeed.com", "indeed.ch"], "https://ch.indeed.com", "indeed", True),
    ("jobsch", "jobs.ch", ["jobs.ch"], "https://www.jobs.ch", "ai", True),
    ("linkedin", "LinkedIn", ["linkedin.com"], "https://www.linkedin.com/jobs", "ai", True),
    (
        "jobroom",
        "Job-Room",
        ["job-room.ch", "arbeit.swiss"],
        "https://www.job-room.ch",
        "ai",
        False,
    ),
]


def upgrade() -> None:
    # La liste des sites n'est plus figée : un identifiant court suffit.
    for table in ("searches", "offer_links"):
        op.drop_constraint(f"{table}_source_check", table)
        op.create_check_constraint(f"{table}_source_check", table, SLUG)
    sites = op.create_table(
        "sites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("senders", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("url", sa.Text()),
        sa.Column("reader", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("builtin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("reader IN ('jobup', 'indeed', 'ai')", name="sites_reader_check"),
        sa.CheckConstraint("slug ~ '^[a-z0-9]{2,30}$'", name="sites_slug_check"),
    )
    op.bulk_insert(
        sites,
        [
            {
                "slug": slug,
                "name": name,
                "senders": senders,
                "url": url,
                "reader": reader,
                "active": active,
                "builtin": reader != "ai",
            }
            for slug, name, senders, url, reader, active in SITES
        ],
    )


def downgrade() -> None:
    op.drop_table("sites")
    for table in ("searches", "offer_links"):
        op.drop_constraint(f"{table}_source_check", table)
        op.create_check_constraint(
            f"{table}_source_check",
            table,
            "source IN ('jobup', 'indeed', 'jobroom', 'unknown')",
        )
