"""Tables de la version 0.1. Les suivantes arrivent avec leurs versions (cadrage §5)."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from jobbot.db.base import Base


class Setting(Base):
    """Réglages métier modifiables dans l'interface (seuils, objectif ORP…)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JobRunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class JobRun(Base):
    """Une exécution de tâche du worker (ou de `jobbot run-job`)."""

    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job: Mapped[str] = mapped_column(Text, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, default=JobRunStatus.RUNNING)
    items_in: Mapped[int | None]
    items_out: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)


# --- Collecte (0.2) -------------------------------------------------------------------


class Source(StrEnum):
    JOBUP = "jobup"
    INDEED = "indeed"
    JOBROOM = "jobroom"
    UNKNOWN = "unknown"


class ParseStatus(StrEnum):
    PARSED = "parsed"  # analysé, au moins une offre
    EMPTY = "empty"  # analysé, aucune offre
    UNRECOGNIZED = "unrecognized"  # aucun analyseur pour cet e-mail
    FAILED = "failed"  # l'analyseur a levé une erreur


class OfferStatus(StrEnum):
    NEW = "new"
    FILTERED_OUT = "filtered_out"
    TO_REVIEW = "to_review"
    LATER = "later"
    IGNORED = "ignored"
    PREPARING = "preparing"
    APPLIED = "applied"


class Search(Base):
    """Une alerte reçue par e-mail = une recherche exécutée par un site (journal ORP)."""

    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text)
    message_id: Mapped[str] = mapped_column(Text, unique=True)
    imap_uid: Mapped[int | None] = mapped_column(BigInteger)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    subject: Mapped[str | None] = mapped_column(Text)
    alert_label: Mapped[str | None] = mapped_column(Text)
    raw_key: Mapped[str] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    results_count: Mapped[int] = mapped_column(default=0)
    new_offers_count: Mapped[int] = mapped_column(default=0)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    job_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_runs.run_id", ondelete="SET NULL")
    )


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    rate_min: Mapped[int | None]
    rate_max: Mapped[int | None]
    snippet: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default=OfferStatus.NEW)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    seen_count: Mapped[int] = mapped_column(default=1)


class OfferLink(Base):
    """Où trouver l'offre : un lien par site."""

    __tablename__ = "offer_links"
    __table_args__ = (UniqueConstraint("offer_id", "source"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)


class OfferSighting(Base):
    """Dans quelles alertes l'offre est apparue."""

    __tablename__ = "offer_sightings"

    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"), primary_key=True
    )
    search_id: Mapped[int] = mapped_column(
        ForeignKey("searches.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    position: Mapped[int]
    # Vrai si l'offre est apparue pour la première fois dans cette alerte.
    is_first: Mapped[bool] = mapped_column(default=False)
