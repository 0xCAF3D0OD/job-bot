"""Canton des offres, pour le filtre par canton de la page Offres

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-05

Le canton vient du lieu (« Pully, VD ») ou, pour une ville seule (jobup), des autres offres
de la même ville qui l'indiquent. Il est ensuite tenu à jour par la tâche `filter`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from jobbot.core.filter import canton_of
from jobbot.core.normalize import normalize_location

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("canton", sa.Text()))
    op.create_index("ix_offers_canton", "offers", ["canton"])
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, location FROM offers")).all()
    known: dict[str, str] = {}
    for _, location in rows:
        canton = canton_of(location)
        if canton:
            known.setdefault(normalize_location(location), canton)
    for offer_id, location in rows:
        canton = canton_of(location) or (
            known.get(normalize_location(location)) if location else None
        )
        if canton:
            bind.execute(
                sa.text("UPDATE offers SET canton = :canton WHERE id = :id"),
                {"canton": canton, "id": offer_id},
            )


def downgrade() -> None:
    op.drop_index("ix_offers_canton", table_name="offers")
    op.drop_column("offers", "canton")
