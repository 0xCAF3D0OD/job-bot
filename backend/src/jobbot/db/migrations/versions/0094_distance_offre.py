"""Filtre « Distance depuis… » : le point de chaque offre (issue #468, Kevin, 18.11.2026)

Revision ID: 0094
Revises: 0093
Create Date: 2026-11-18

Nouvelles colonnes `offers.latitude` et `offers.longitude`, tirées du lieu de l'annonce par
`jobbot.core.geo.locate` (numéros postaux suisses de GeoNames, copie figée dans
`jobbot/data/geonames/`, aucun appel externe). Vides quand le lieu n'est pas reconnu sans
ambiguïté : l'offre va dans « Lieu non précisé ». Comme 0007 (canton), la migration se sert du code
de l'application : la table de lieux est un fichier du dépôt, versionné avec lui. Le compte des
offres situées et non situées est écrit dans le journal de la migration.

Données (docs/regles-securite-donnees.md) : une valeur dérivée d'une colonne de `offers` (le lieu de
l'annonce, pas l'adresse de la personne), même niveau « Personnelle » (D-1), cloisonnée par la RLS
de la table, exportée et effacée avec la ligne.
Retour arrière : les colonnes sont retirées, `location` ne change pas.
"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from jobbot.core.geo import locate

revision: str = "0094"
down_revision: str | None = "0093"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    op.add_column("offers", sa.Column("latitude", sa.Double()))
    op.add_column("offers", sa.Column("longitude", sa.Double()))
    bind = op.get_bind()
    places = [
        row.location
        for row in bind.execute(
            sa.text("SELECT DISTINCT location FROM offers WHERE location IS NOT NULL")
        )
    ]
    for place in places:
        point = locate(place)
        if point:
            bind.execute(
                sa.text(
                    "UPDATE offers SET latitude = :lat, longitude = :lon WHERE location = :place"
                ),
                {"lat": point.lat, "lon": point.lon, "place": place},
            )
    row = bind.execute(
        sa.text(
            "SELECT count(latitude) AS located, count(*) - count(latitude) AS unknown FROM offers"
        )
    ).one()
    log.info("Distance des offres : %s situées, %s lieu non précisé", row.located, row.unknown)


def downgrade() -> None:
    op.drop_column("offers", "longitude")
    op.drop_column("offers", "latitude")
