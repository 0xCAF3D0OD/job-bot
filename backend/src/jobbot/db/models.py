"""Tables de la version 0.1. Les suivantes arrivent avec leurs versions (cadrage §5)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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
    # Lecture de la page de l'offre (jobup seulement, docs/05).
    apply_url: Mapped[str | None] = mapped_column(Text)
    apply_kind: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    employment_type: Mapped[str | None] = mapped_column(Text)
    enrich_status: Mapped[str] = mapped_column(Text, default="pending")
    # Canton (« VD »), déduit du lieu ou appris des autres offres de la même ville.
    canton: Mapped[str | None] = mapped_column(Text, index=True)
    enrich_attempts: Mapped[int] = mapped_column(default=0)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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


# --- Prérequis et filtre (0.3) --------------------------------------------------------


class Criterion(Base):
    """Une règle de prérequis par ligne (docs/04 §8), valeur en JSON."""

    __tablename__ = "criteria"

    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Evaluation(Base):
    """Résultat du filtre pour une offre ; la note IA s'y ajoutera en 0.4."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), unique=True)
    filter_passed: Mapped[bool]
    # Liste de {"rule": …, "message": …}
    filter_reasons: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    criteria_hash: Mapped[str] = mapped_column(Text)
    # Note et résumé de l'IA (0.4).
    score: Mapped[int | None] = mapped_column(SmallInteger)
    summary_role: Mapped[str | None] = mapped_column(Text)
    summary_asks: Mapped[str | None] = mapped_column(Text)
    summary_offers: Mapped[str | None] = mapped_column(Text)
    # Vrai si le résumé est fait sur l'extrait de l'alerte, faute de texte complet.
    summary_partial: Mapped[bool] = mapped_column(default=False)
    strengths: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    gaps: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    profile_hash: Mapped[str | None] = mapped_column(Text)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score_error: Mapped[str | None] = mapped_column(Text)
    # Notification ntfy envoyée pour cette note (une seule fois par offre).
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --- Documents et blocs de profil (0.3) -----------------------------------------------


class ChunkKind(StrEnum):
    EXPERIENCE = "experience"
    COMPETENCE = "competence"
    FORMATION = "formation"
    PREFERENCE = "preference"
    REDHIBITOIRE = "redhibitoire"
    TON = "ton"


class Document(Base):
    """Document déposé par Kevin (CV, certificats…). Le fichier est dans le stockage."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(Text)
    size: Mapped[int]
    sha256: Mapped[str] = mapped_column(Text, unique=True)
    storage_key: Mapped[str] = mapped_column(Text)
    text_status: Mapped[str] = mapped_column(Text)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProfileChunk(Base):
    """Bloc de profil : la seule source de vérité de l'IA sur Kevin (cadrage §3)."""

    __tablename__ = "profile_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EnrichStatus(StrEnum):
    PENDING = "pending"
    OK = "ok"
    EXPIRED = "expired"
    FAILED = "failed"
    SKIPPED = "skipped"  # pas de page lisible (offre Indeed)


# --- Note IA (0.4) --------------------------------------------------------------------


class LlmCall(Base):
    """Un appel facturé à l'IA (direct ou résultat d'un lot), pour le budget mensuel."""

    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purpose: Mapped[str] = mapped_column(Text)
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id", ondelete="SET NULL"))
    model: Mapped[str] = mapped_column(Text)
    batch_id: Mapped[str | None] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(default=0)
    cache_read_tokens: Mapped[int] = mapped_column(default=0)
    cache_write_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 5))
    cost_chf: Mapped[Decimal] = mapped_column(Numeric(10, 5))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class LlmBatch(Base):
    """Lot de notes envoyé à l'API (rattrapage, renotation) : moitié prix, résultat différé."""

    __tablename__ = "llm_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_batch_id: Mapped[str] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(Text, default="in_progress")  # in_progress|ended|failed
    offer_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# --- Candidatures (0.5) ---------------------------------------------------------------


class ApplicationMethod(StrEnum):
    """Mode de candidature, au sens du formulaire ORP."""

    ELECTRONIQUE = "electronique"
    ECRIT = "ecrit"
    TELEPHONE = "telephone"
    PERSONNEL = "personnel"


class ApplicationStatus(StrEnum):
    EN_ATTENTE = "en_attente"
    RELANCEE = "relancee"
    ENTRETIEN = "entretien"
    REFUS = "refus"
    ENGAGEMENT = "engagement"
    SANS_REPONSE = "sans_reponse"


class Application(Base):
    """Une candidature envoyée par Kevin : suivi et données du formulaire ORP (docs/08)."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"), unique=True
    )
    sent_at: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(Text)
    assigned_by_orp: Mapped[bool] = mapped_column(default=False)
    company: Mapped[str] = mapped_column(Text)
    company_address: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(Text)
    contact_phone: Mapped[str | None] = mapped_column(Text)
    job_title: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    # « plein temps » ou « temps partiel (80 %) », comme sur le formulaire ORP.
    rate_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default=ApplicationStatus.EN_ATTENTE)
    status_reason: Mapped[str | None] = mapped_column(Text)
    status_at: Mapped[date | None] = mapped_column(Date)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    orp_month: Mapped[str] = mapped_column(Text, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
