"""Tables de la version 0.1. Les suivantes arrivent avec leurs versions (cadrage §5)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    ColumnElement,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    and_,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from jobbot.db.base import Base

# Compte de la ligne (docs/65) : tiré du compte en cours ; la base ne montre que les siennes.
CURRENT_ACCOUNT = text("nullif(current_setting('app.user_id', true), '')::bigint")


def account_column() -> Mapped[int]:
    return mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        server_default=CURRENT_ACCOUNT,
        index=True,
    )


class Setting(Base):
    """Réglages métier modifiables dans l'interface (seuils, objectif ORP…)."""

    __tablename__ = "settings"

    user_id: Mapped[int] = account_column()

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
    # Les comptes pour qui la tâche a échoué (docs/78 §3.4).
    failed_accounts: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))


# --- Collecte (0.2) -------------------------------------------------------------------


class Source(StrEnum):
    JOBUP = "jobup"
    INDEED = "indeed"
    JOBROOM = "jobroom"
    JOBSCH = "jobsch"
    LINKEDIN = "linkedin"
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

    user_id: Mapped[int] = account_column()

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
    # Recommandations écartées, hors métier (docs/116 §3).
    off_topic_count: Mapped[int] = mapped_column(default=0, server_default="0")
    # Un site demande de confirmer l'alerte (docs/65 §3) : son lien, et quand c'est fait.
    confirm_url: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Autre chose qu'une alerte (docs/112) : « code » de vérification ou « message » du site ;
    # le code lu est effacé au bout de 30 minutes.
    kind: Mapped[str | None] = mapped_column(Text, index=True)
    code: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    job_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_runs.run_id", ondelete="SET NULL")
    )


# Une recherche publique faite par jobA1 (docs/104, 0.80.0) se range dans le journal, mais
# n'est pas une alerte reçue : ni preuve de recherche ORP, ni signe qu'une alerte marche. De
# même pour un code ou un message d'un site (docs/112).
PUBLIC_SEARCH_PREFIX = "public:"


def received_alert() -> ColumnElement[bool]:
    return and_(Search.message_id.not_like(f"{PUBLIC_SEARCH_PREFIX}%"), Search.kind.is_(None))


class Offer(Base):
    __tablename__ = "offers"

    user_id: Mapped[int] = account_column()

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
    # Offre retirée (docs/10 §1) : page jobup introuvable (« page ») ou plus vue dans aucune
    # alerte depuis 30 jours (« age », pour les sites qu'on ne peut pas vérifier).
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expiry_source: Mapped[str | None] = mapped_column(Text)
    # Choix de Kevin (docs/11 §1) : « expired » ou « alive », prioritaire sur la détection.
    expiry_override: Mapped[str | None] = mapped_column(Text)
    # Adresse de l'entreprise (docs/12 §2) et sa source : page, registry, letter ou manual.
    company_address: Mapped[str | None] = mapped_column(Text)
    company_address_source: Mapped[str | None] = mapped_column(Text)
    # Page où l'IA a trouvé l'adresse (source « web »), pour vérifier d'un clic.
    company_address_url: Mapped[str | None] = mapped_column(Text)
    # Logo relevé sur la page de l'offre ou dans l'e-mail d'alerte, et site de l'entreprise
    # (docs/14 §4) ; le logo lui-même est téléchargé une fois par entreprise.
    logo_url: Mapped[str | None] = mapped_column(Text)
    company_website: Mapped[str | None] = mapped_column(Text)
    # Candidature spontanée (docs/39) : offre créée par toi, sans annonce ; jamais notée.
    spontaneous: Mapped[bool] = mapped_column(default=False, server_default=false())
    spontaneous_reason: Mapped[str | None] = mapped_column(Text)
    # Annonce chez l'employeur (docs/20 §2) : adresse vérifiée, d'où elle vient
    # (site | ats | web), résultat de la recherche (found | not_found | agency | gone).
    employer_url: Mapped[str | None] = mapped_column(Text)
    employer_url_source: Mapped[str | None] = mapped_column(Text)
    employer_status: Mapped[str | None] = mapped_column(Text)
    employer_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Dernière revérification de la page jobup.
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Offres douteuses (docs/30) : doublon rattaché à l'offre gardée (caché des listes), et
    # première apparition de l'annonce, doublons compris (« annonce permanente »).
    duplicate_of: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"), index=True
    )
    seen_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OfferLink(Base):
    """Où trouver l'offre : un lien par site."""

    __tablename__ = "offer_links"

    user_id: Mapped[int] = account_column()
    __table_args__ = (UniqueConstraint("user_id", "offer_id", "source"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)


class OfferSighting(Base):
    """Dans quelles alertes l'offre est apparue."""

    __tablename__ = "offer_sightings"

    user_id: Mapped[int] = account_column()

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

    user_id: Mapped[int] = account_column()

    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Evaluation(Base):
    """Résultat du filtre pour une offre ; la note IA s'y ajoutera en 0.4."""

    __tablename__ = "evaluations"
    __table_args__ = (UniqueConstraint("user_id", "offer_id"),)

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
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
    # Étiquettes des cartes (docs/11 §3) ; keywords_asks : [{text, covered}].
    keywords_role: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    keywords_asks: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    keywords_offers: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    # Télétravail relevé par l'IA (docs/26 §2) : onsite | hybrid | full | unknown ; jours par
    # semaine (partiel) ; d'où on peut travailler (« Europe », « US only ») et si c'est ouvert
    # depuis la Suisse (None : non précisé).
    remote: Mapped[str | None] = mapped_column(Text)
    remote_days: Mapped[int | None] = mapped_column(SmallInteger)
    remote_region: Mapped[str | None] = mapped_column(Text)
    remote_from_switzerland: Mapped[bool | None]
    # Signes d'arnaque relevés par l'IA à la notation (docs/30 §2) : [{reason, excerpt}].
    scam_signals: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
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

    user_id: Mapped[int] = account_column()

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
    # « certificate » : un certificat de travail, lu par jobA1 (docs/87).
    kind: Mapped[str | None] = mapped_column(Text)


class ScoreCorrection(Base):
    """« Cette note ne me correspond pas » (docs/114) : une correction par offre, et le bloc de
    profil qu'elle a ajouté, le cas échéant."""

    __tablename__ = "score_corrections"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "offer_id"],
            ["offers.user_id", "offers.id"],
            name="score_corrections_offer_id_fkey",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["user_id", "chunk_id"],
            ["profile_chunks.user_id", "profile_chunks.id"],
            name="score_corrections_chunk_id_fkey",
            ondelete="SET NULL",
        ),
        UniqueConstraint("user_id", "offer_id", name="score_corrections_offer_key"),
    )

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(BigInteger)
    # « high » (trop haute) ou « low » (trop basse).
    direction: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    score_before: Mapped[int | None] = mapped_column(SmallInteger)
    chunk_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CertificateReading(Base):
    """La lecture d'un certificat de travail (docs/87) : les formules repérées, la note, le
    conseil ; la lecture de l'IA si elle a été demandée."""

    __tablename__ = "certificate_readings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "document_id"],
            ["documents.user_id", "documents.id"],
            name="certificate_readings_document_id_fkey",
            ondelete="CASCADE",
        ),
        UniqueConstraint("user_id", "document_id", name="certificate_readings_document_key"),
    )

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(BigInteger)
    language: Mapped[str | None] = mapped_column(Text)
    # 4 très bon, 3 bon, 2 suffisant, 1 à revoir ; None sans formule de prestation.
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    # attach | on_request | correct
    advice: Mapped[str] = mapped_column(Text)
    passages: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    notes: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    rules_version: Mapped[str] = mapped_column(Text)
    ai: Mapped[Any | None] = mapped_column(JSONB)
    ai_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProfileChunk(Base):
    """Bloc de profil : la seule source de vérité de l'IA sur Kevin (cadrage §3)."""

    __tablename__ = "profile_chunks"

    user_id: Mapped[int] = account_column()

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
    # D'où vient le bloc : « correction » s'il a été ajouté en corrigeant une note (docs/114).
    origin: Mapped[str | None] = mapped_column(Text)


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

    user_id: Mapped[int] = account_column()

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

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_batch_id: Mapped[str] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(Text, default="in_progress")  # in_progress|ended|failed
    offer_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger))
    # Consignes avec lesquelles le lot a été envoyé (« score-v1 », « score-v2 »…).
    prompt_version: Mapped[str] = mapped_column(Text, default="score-v1")
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
    __table_args__ = (UniqueConstraint("user_id", "offer_id"),)

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Une candidature par offre, dans le compte (migration 0055).
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id", ondelete="SET NULL"))
    sent_at: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(Text)
    assigned_by_orp: Mapped[bool] = mapped_column(default=False)
    company: Mapped[str] = mapped_column(Text)
    company_address: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(Text)
    contact_phone: Mapped[str | None] = mapped_column(Text)
    # Demandé par le formulaire de saisie de Job-Room.
    contact_email: Mapped[str | None] = mapped_column(Text)
    # Date d'entretien pour laquelle le rappel « fais le point » est parti (docs/23 §1).
    interview_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    job_title: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    # « plein temps » ou « temps partiel (80 %) », comme sur le formulaire ORP.
    rate_text: Mapped[str | None] = mapped_column(Text)
    # Formulaire de candidature ou annonce (ou e-mail utilisé), demandé par l'ORP (docs/13).
    application_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default=ApplicationStatus.EN_ATTENTE)
    status_reason: Mapped[str | None] = mapped_column(Text)
    status_at: Mapped[date | None] = mapped_column(Date)
    # Date de la relance (docs/38) : « Sans réponse » proposé 14 jours après.
    followed_up_at: Mapped[date | None] = mapped_column(Date)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    orp_month: Mapped[str] = mapped_column(Text, index=True)
    # Saisie dans Job-Room le … (docs/70 §6) : par l'extension ou « Marquer comme déclarée ».
    job_room_at: Mapped[date | None] = mapped_column(Date)
    # Documents envoyés (docs/08 §5), retéléchargeables depuis la page Candidatures.
    letter_draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("drafts.id", ondelete="SET NULL")
    )
    cv_draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DraftKind(StrEnum):
    LETTER = "letter"
    CV = "cv"


class Draft(Base):
    """Une version de lettre (ou de CV) préparée pour une offre (docs/08 §3).

    `content` pour une lettre : {subject, paragraphs: [{text, chunk_ids}], employer: {...}}.
    Les coordonnées de Kevin n'y sont jamais : elles sont ajoutées à l'affichage.
    """

    __tablename__ = "drafts"

    user_id: Mapped[int] = account_column()
    __table_args__ = (UniqueConstraint("user_id", "offer_id", "kind", "version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(Text)
    content: Mapped[Any] = mapped_column(JSONB)
    instruction: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OrpMonth(Base):
    """État de la remise des preuves ORP d'un mois (docs/09 §4)."""

    __tablename__ = "orp_months"

    user_id: Mapped[int] = account_column()

    month: Mapped[str] = mapped_column(Text, primary_key=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_after_submit: Mapped[bool] = mapped_column(default=False)
    # Rappels ntfy déjà envoyés (0.6.0-b) : {"under_target": date, "due": date, "eve": date}.
    reminders_sent: Mapped[Any] = mapped_column(JSONB, default=dict)


class OrpMeeting(Base):
    """Un rendez-vous avec le conseiller ORP (docs/83) : sa date, et les questions préparées."""

    __tablename__ = "orp_meetings"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # Lieu ou « visio » ; conseiller : facultatifs.
    place: Mapped[str | None] = mapped_column(Text)
    advisor: Mapped[str | None] = mapped_column(Text)
    # Questions au conseiller : [{key, text, checked}] ; `key` relie une question proposée à sa
    # règle (« funding:12 »), « custom:… » pour une question écrite à la main.
    questions: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Après le rendez-vous (0.67.2) : ce qui a été convenu, noté quand `outcome_at` est rempli.
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    agreed_target: Mapped[int | None] = mapped_column(Integer)
    # Mesures accordées : [{text, training_id}] ; une formation liée passe en « financement
    # accepté ».
    measures: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    assignments: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    # Rappel de la veille envoyé pour cette date : une date changée est rappelée à nouveau.
    reminded_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # La feuille rédigée par l'IA, sur demande.
    sheet_text: Mapped[str | None] = mapped_column(Text)


class Company(Base):
    """Recherche d'une entreprise dans le registre IDE, mise en cache (docs/12 §2.2)."""

    __tablename__ = "companies"

    # Nom normalisé, sans forme juridique : « moser vernet » pour « Moser Vernet & Cie SA ».
    name_key: Mapped[str] = mapped_column(Text, primary_key=True)
    uid: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    # Jusqu'à 3 propositions : {uid, name, street, zip_code, town, canton, active, address}.
    candidates: Mapped[Any] = mapped_column(JSONB, default=list)
    # « auto » : correspondance sûre ; « manual » : choisie par Kevin ; « web » : trouvée sur
    # Internet par l'IA ; None : à choisir.
    chosen_by: Mapped[str | None] = mapped_column(Text)
    looked_up_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Recherche sur Internet (0.7.2), faute de correspondance sûre dans le registre.
    source_url: Mapped[str | None] = mapped_column(Text)
    web_looked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Page carrières et outil de recrutement reconnu (« greenhouse:gitlab »), docs/20 §2.
    careers_url: Mapped[str | None] = mapped_column(Text)
    ats: Mapped[str | None] = mapped_column(Text)
    careers_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SiteReader(StrEnum):
    """Comment lire les alertes d'un site (docs/11 §2)."""

    JOBUP = "jobup"  # analyseur intégré
    INDEED = "indeed"  # analyseur intégré
    AI = "ai"  # l'IA lit l'e-mail d'alerte


class Site(Base):
    """Un site dont les alertes sont suivies : intégré (jobup, Indeed) ou ajouté par Kevin."""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Identifiant court, repris dans searches.source et offer_links.source.
    slug: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    # Adresses d'expédition des alertes ou domaines (« noreply@jobs.ch », « jobs.ch »).
    senders: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    url: Mapped[str | None] = mapped_column(Text)
    reader: Mapped[str] = mapped_column(Text)
    builtin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AccountSite(Base):
    """Un site en pause pour un compte (docs/65) ; sans ligne, le site est suivi."""

    __tablename__ = "account_sites"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        server_default=CURRENT_ACCOUNT,
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True
    )
    active: Mapped[bool] = mapped_column()


class CompanyLogo(Base):
    """Logo téléchargé d'une entreprise (nom normalisé), servi par la plateforme."""

    __tablename__ = "company_logos"

    name_key: Mapped[str] = mapped_column(Text, primary_key=True)
    # Fichier dans le stockage (logos/…), None si aucun logo utilisable n'a été trouvé.
    storage_key: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    """Alerte de la cloche (docs/15 §1) : la même que sur le téléphone, gardée 90 jours."""

    __tablename__ = "notifications"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # offers, follow_up, orp_target, orp_due, budget, collect_failed
    kind: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text, default="")
    # Page de la plateforme à ouvrir (« /candidatures?vue=orp&mois=2026-09 »).
    link: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NewsSource(Base):
    """Source d'actualités (docs/15 §2) : flux RSS d'un site ou d'une chaîne YouTube."""

    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(Text)  # articles | videos
    name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    feed_url: Mapped[str] = mapped_column(Text, unique=True)
    # Ne garder que les entrées dont l'auteur, le titre ou le texte contient ce texte.
    match: Mapped[str | None] = mapped_column(Text)
    # Pays (CH, FR, BE…, INT pour international) et langue (fr, de, en…) : filtres (docs/16 §3).
    country: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    # Toujours visible, même filtré sur « Mon domaine » (docs/16 §2).
    labour_market: Mapped[bool] = mapped_column(default=False)
    # Veille par recherche (docs/16 §4.2) : mots-clés suivis dans Google Actualités.
    query: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsItem(Base):
    """Article ou vidéo relevé dans une source, gardé 60 jours."""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, unique=True)
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    # Miniature téléchargée par la plateforme (news/…), servie sans appel au site d'origine.
    image_key: Mapped[str | None] = mapped_column(Text)
    # Langue du contenu, déduite du texte, sinon celle du flux ou de la source.
    language: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Training(Base):
    """Formation du catalogue (docs/16 §5) : vérifiée (catalogue du dépôt) ou suggérée par l'IA."""

    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)  # certification | cours | parcours | atelier
    format: Mapped[str] = mapped_column(Text)  # self_paced | live | in_person | exam | exam_online
    language: Mapped[str] = mapped_column(Text)
    price: Mapped[str] = mapped_column(Text)  # free | paid
    duration: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str | None] = mapped_column(Text)  # beginner | intermediate | advanced
    # Unique par profil (docs/17) : une fois dans le catalogue, une fois par profil au plus.
    url: Mapped[str] = mapped_column(Text)
    # Mots-clés de la formation (Kubernetes, CKA…), comparés à « Mon domaine ».
    tags: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    prep: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(Text)  # catalog | ai
    # Suggestion de l'IA : profil qui l'a demandée ; vide pour le catalogue.
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    # Suggestion de l'IA : à vérifier tant que Kevin ne l'a pas gardée ; écartée, elle reste
    # en base pour ne pas être reproposée.
    verified: Mapped[bool] = mapped_column(default=True)
    dismissed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrainingMark(Base):
    """Suivi d'une formation : intéressé, en cours (progression libre), terminée."""

    __tablename__ = "training_marks"

    user_id: Mapped[int] = account_column()

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    training_id: Mapped[int] = mapped_column(
        ForeignKey("trainings.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(Text)  # interested | in_progress | done
    progress: Mapped[str | None] = mapped_column(Text)
    done_at: Mapped[date | None] = mapped_column(Date)
    certified: Mapped[bool | None]
    # Bloc « formation » créé depuis la formation terminée (docs/37 §1).
    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("profile_chunks.id", ondelete="SET NULL")
    )
    # Demande de financement à l'ORP (docs/37 §2) : requested | accepted | refused.
    funding_status: Mapped[str | None] = mapped_column(Text)
    funding_requested_at: Mapped[date | None] = mapped_column(Date)
    funding_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Profile(Base):
    """Profil d'essai (docs/17) : « Mon domaine », filtres et sources des Actualités.

    Le profil principal est celui de Kevin ; les autres sont fictifs, pour juger si les
    Actualités et les Formations conviennent à d'autres chercheurs d'emploi.
    """

    __tablename__ = "profiles"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    occupation: Mapped[str | None] = mapped_column(Text)
    is_main: Mapped[bool] = mapped_column(default=False)
    # domain_keywords, domain_only, countries, languages (docs/16 §2-3).
    preferences: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    news_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProfileSource(Base):
    """Source d'actualités suivie par un profil ; une source sans abonné actif n'est pas relevée."""

    __tablename__ = "profile_sources"

    user_id: Mapped[int] = account_column()

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("news_sources.id", ondelete="CASCADE"), primary_key=True
    )
    active: Mapped[bool] = mapped_column(default=True)


class User(Base):
    """Compte de connexion (docs/18 §1, docs/65) : le premier est l'exploitant, les autres
    sont invités par lui ou demandés depuis la page de connexion (docs/102)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    # scrypt$n$r$p$sel$empreinte (base64) : jamais le mot de passe en clair.
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Fixé par l'exploitant (docs/65 §4) ; vide : le plafond par défaut d'un compte invité.
    ai_budget_chf: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    # Suspendu : plus de connexion ni de tâches, données gardées.
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Adresse de réception d'un compte invité : boite+code@domaine (docs/65 §3).
    mail_code: Mapped[str | None] = mapped_column(Text, unique=True)
    # Accepté par l'exploitant (docs/102) ; vide : une demande de compte en attente, sans
    # connexion ni tâches. Un compte invité ou créé autrement est accepté d'office.
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Le mot laissé avec la demande, effacé à l'acceptation.
    signup_note: Mapped[str | None] = mapped_column(Text)


class AccountLink(Base):
    """Lien à usage unique (docs/65 §2) : invitation (7 jours) ou réinitialisation (24 h)."""

    __tablename__ = "account_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlatformSetting(Base):
    """Réglage de l'installation, commun à tous les comptes (plafond total de l'IA)."""

    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB)


class UserSession(Base):
    """Session ouverte par une connexion ; le cookie porte le jeton, la base son empreinte."""

    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(Text)


class AlertSearch(Base):
    """Recherche à suivre par une alerte e-mail (docs/20 §1) : des mots et un lieu."""

    __tablename__ = "alert_searches"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terms: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertSetup(Base):
    """« J'ai créé l'alerte » : la recherche est suivie sur ce site."""

    __tablename__ = "alert_setups"

    user_id: Mapped[int] = account_column()

    search_id: Mapped[int] = mapped_column(
        ForeignKey("alert_searches.id", ondelete="CASCADE"), primary_key=True
    )
    site: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Interview(Base):
    """Retour d'entretien (docs/23) : déroulé, ressenti, questions, enseignements, suite."""

    __tablename__ = "interviews"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str | None] = mapped_column(Text)
    held_at: Mapped[date | None] = mapped_column(Date)
    format: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[str | None] = mapped_column(Text)
    interviewers: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    people_count: Mapped[int | None] = mapped_column(SmallInteger)
    rating: Mapped[int] = mapped_column(SmallInteger)
    stress: Mapped[int | None] = mapped_column(SmallInteger)
    interest: Mapped[str | None] = mapped_column(Text)
    outlook: Mapped[str | None] = mapped_column(Text)
    # [{text, difficult}]
    questions: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    salary_asked: Mapped[bool | None]
    salary_answer: Mapped[str | None] = mapped_column(Text)
    went_well: Mapped[str | None] = mapped_column(Text)
    went_badly: Mapped[str | None] = mapped_column(Text)
    to_prepare: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    my_questions: Mapped[str | None] = mapped_column(Text)
    missed_questions: Mapped[str | None] = mapped_column(Text)
    learned: Mapped[str | None] = mapped_column(Text)
    warnings: Mapped[str | None] = mapped_column(Text)
    next_step: Mapped[str | None] = mapped_column(Text)
    next_step_at: Mapped[date | None] = mapped_column(Date)
    thanks: Mapped[str | None] = mapped_column(Text)
    employer_feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterviewPractice(Base):
    """Entretien blanc avec l'IA (docs/75) : jamais compté comme un vrai entretien."""

    __tablename__ = "interview_practices"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Sans candidature : un entretien type, d'après le profil.
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="en_cours")
    # [{role: recruteur|candidat, text, question, relance, skipped}]
    turns: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    feedback: Mapped[Any | None] = mapped_column(JSONB)
    cost_chf: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=Decimal(0))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChatConversation(Base):
    """Discussion avec l'assistant (docs/24 §4), gardée 30 jours après la dernière réplique."""

    __tablename__ = "chat_conversations"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class ChatMessage(Base):
    """Réplique d'une discussion : texte seulement (les lectures de données ne sont pas gardées)."""

    __tablename__ = "chat_messages"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("chat_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(Text)  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    # Page ouverte au moment de la question (/candidatures/suivi…).
    page: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatAction(Base):
    """Action proposée par l'assistant (docs/52) : faite seulement sur confirmation de Kevin.

    `previous` garde l'état d'avant pour « Annuler ».
    """

    __tablename__ = "chat_actions"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("chat_conversations.id", ondelete="CASCADE"), index=True
    )
    # offer_status | offer_expiry | application_status
    kind: Mapped[str] = mapped_column(Text)
    target_id: Mapped[int] = mapped_column(BigInteger)
    value: Mapped[str] = mapped_column(Text)
    previous: Mapped[Any] = mapped_column(JSONB)
    label: Mapped[str] = mapped_column(Text)
    # proposed | done | undone | declined | stale
    state: Mapped[str] = mapped_column(Text, server_default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CalendarToken(Base):
    """Abonnement d'agenda (docs/40) : jeton secret révocable ; seule son empreinte est gardée."""

    __tablename__ = "calendar_tokens"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    # Adresse de la plateforme vue par le navigateur (tunnel, https), pour les liens.
    origin: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExtensionToken(Base):
    """Jeton de l'extension du navigateur (docs/25 §4) : seule son empreinte est gardée."""

    __tablename__ = "extension_tokens"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Jeton de liaison (« Relier ce navigateur ») : à lire dans les 2 minutes, puis effacé à la
    # première utilisation (docs/76 §1).
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Contact(Base):
    """Prise de contact dans l'entreprise (docs/31 §4) : rattachée à l'offre et/ou à la candidature.
    Le nom de la personne reste ici ; il n'est jamais envoyé à l'IA."""

    __tablename__ = "contacts"

    user_id: Mapped[int] = account_column()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)  # recruiter | manager | team | alumni | other
    # linkedin_invite | linkedin_message | email | phone | other
    channel: Mapped[str] = mapped_column(Text)
    contacted_on: Mapped[date] = mapped_column(Date)
    answered_on: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
