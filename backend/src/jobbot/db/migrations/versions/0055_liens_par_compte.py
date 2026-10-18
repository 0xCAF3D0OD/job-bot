"""Aucun lien entre deux comptes (docs/78 §3.3)

Revision ID: 0055
Revises: 0054
Create Date: 2026-10-18

Les 21 clés étrangères entre tables personnelles comprennent désormais le compte : une ligne
ne peut désigner qu'une ligne du **même** compte, et la base refuse sinon. Avant, elle
vérifiait seulement que le numéro existait, quel que soit son compte.

Un lien qui traverserait déjà deux comptes (il ne devrait pas y en avoir) est défait s'il est
facultatif ; s'il est obligatoire, la migration s'arrête et dit lequel, sans rien effacer.

`ON DELETE SET NULL (colonne)` demande PostgreSQL 15 ou plus récent.

Les quatre unicités rattachées à une offre (une candidature, une évaluation par offre…)
valent par compte.

Le journal des tâches retient aussi les comptes pour qui une tâche a échoué (docs/78 §3.4) :
chacun voit son échec, et seul l'exploitant le détail.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "0055"
down_revision: str | None = "0054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PARENTS = (
    "offers",
    "searches",
    "documents",
    "drafts",
    "profile_chunks",
    "profiles",
    "alert_searches",
    "applications",
    "chat_conversations",
)
# (table, colonne, table désignée, effacement : cascade ou set null, colonne obligatoire)
LINKS = (
    ("offers", "duplicate_of", "offers", "set null", False),
    ("offer_links", "offer_id", "offers", "cascade", True),
    ("offer_sightings", "offer_id", "offers", "cascade", True),
    ("offer_sightings", "search_id", "searches", "cascade", True),
    ("evaluations", "offer_id", "offers", "cascade", True),
    ("profile_chunks", "document_id", "documents", "set null", False),
    ("llm_calls", "offer_id", "offers", "set null", False),
    ("applications", "cv_draft_id", "drafts", "set null", False),
    ("applications", "letter_draft_id", "drafts", "set null", False),
    ("applications", "offer_id", "offers", "set null", False),
    ("drafts", "offer_id", "offers", "cascade", True),
    ("training_marks", "chunk_id", "profile_chunks", "set null", False),
    ("training_marks", "profile_id", "profiles", "cascade", True),
    ("profile_sources", "profile_id", "profiles", "cascade", True),
    ("alert_setups", "search_id", "alert_searches", "cascade", True),
    ("interviews", "application_id", "applications", "cascade", True),
    ("chat_messages", "conversation_id", "chat_conversations", "cascade", True),
    ("contacts", "application_id", "applications", "cascade", False),
    ("contacts", "offer_id", "offers", "cascade", False),
    ("chat_actions", "conversation_id", "chat_conversations", "cascade", True),
    ("interview_practices", "application_id", "applications", "set null", False),
)


# Unicités qui valaient pour toute la plateforme : par compte, pour qu'un refus ne dise pas à
# un compte qu'une ligne existe chez un autre (une candidature pour cette offre…).
UNIQUES = (
    ("applications", "applications_offer_id_key", "offer_id"),
    ("evaluations", "evaluations_offer_id_key", "offer_id"),
    ("offer_links", "offer_links_offer_id_source_key", "offer_id, source"),
    ("drafts", "drafts_offer_id_kind_version_key", "offer_id, kind, version"),
)


def _name(table: str, column: str) -> str:
    return f"{table}_{column}_fkey"


def _crossing(table: str, column: str, parent: str) -> str:
    return (
        f"from {table} c where c.{column} is not null and not exists "
        f"(select 1 from {parent} p where p.id = c.{column} and p.user_id = c.user_id)"
    )


def upgrade() -> None:
    op.add_column("job_runs", sa.Column("failed_accounts", ARRAY(sa.BigInteger())))
    bind = op.get_bind()
    for table, name, columns in UNIQUES:
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(f"alter table {table} add constraint {name} unique (user_id, {columns})")
    for parent in PARENTS:
        op.execute(
            f"alter table {parent} add constraint {parent}_user_id_id_key unique (user_id, id)"
        )
    for table, column, parent, on_delete, required in LINKS:
        crossing = _crossing(table, column, parent)
        if required:
            found = bind.execute(sa.text(f"select count(*) {crossing}")).scalar_one()
            if found:
                raise RuntimeError(
                    f"{found} ligne(s) de {table} désignent une ligne de {parent} d'un autre "
                    f"compte ({column}) : à corriger avant la migration (docs/78 §3.3)"
                )
        else:
            op.execute(
                f"update {table} set {column} = null where ctid in (select c.ctid {crossing})"
            )
        action = "cascade" if on_delete == "cascade" else f"set null ({column})"
        op.execute(f"alter table {table} drop constraint {_name(table, column)}")
        op.execute(
            f"alter table {table} add constraint {_name(table, column)} "
            f"foreign key (user_id, {column}) references {parent} (user_id, id) "
            f"on delete {action}"
        )


def downgrade() -> None:
    op.drop_column("job_runs", "failed_accounts")
    for table, column, parent, on_delete, _required in LINKS:
        op.execute(f"alter table {table} drop constraint {_name(table, column)}")
        op.execute(
            f"alter table {table} add constraint {_name(table, column)} "
            f"foreign key ({column}) references {parent} (id) on delete {on_delete}"
        )
    for parent in PARENTS:
        op.execute(f"alter table {parent} drop constraint {parent}_user_id_id_key")
    for table, name, columns in UNIQUES:
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(f"alter table {table} add constraint {name} unique ({columns})")
