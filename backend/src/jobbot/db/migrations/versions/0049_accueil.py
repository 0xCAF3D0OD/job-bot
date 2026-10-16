"""L'accueil après la première connexion (docs/66 §4)

Revision ID: 0049
Revises: 0048
Create Date: 2026-10-16

Les comptes déjà là (l'exploitant, et ceux qui utilisent déjà la plateforme) sont marqués
« accueil fait » : seuls les comptes créés ensuite le verront.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "insert into settings (user_id, key, value) "
        """select id, 'welcome', '{"done": true}'::jsonb from users """
        "on conflict (user_id, key) do nothing"
    )


def downgrade() -> None:
    op.execute("delete from settings where key = 'welcome'")
