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
    Integer,
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
    # Dernière revérification de la page jobup.
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
    # Étiquettes des cartes (docs/11 §3) ; keywords_asks : [{text, covered}].
    keywords_role: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    keywords_asks: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    keywords_offers: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
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
    # Formulaire de candidature ou annonce (ou e-mail utilisé), demandé par l'ORP (docs/13).
    application_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default=ApplicationStatus.EN_ATTENTE)
    status_reason: Mapped[str | None] = mapped_column(Text)
    status_at: Mapped[date | None] = mapped_column(Date)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    orp_month: Mapped[str] = mapped_column(Text, index=True)
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
    __table_args__ = (UniqueConstraint("offer_id", "kind", "version"),)

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

    month: Mapped[str] = mapped_column(Text, primary_key=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_after_submit: Mapped[bool] = mapped_column(default=False)
    # Rappels ntfy déjà envoyés (0.6.0-b) : {"under_target": date, "due": date, "eve": date}.
    reminders_sent: Mapped[Any] = mapped_column(JSONB, default=dict)


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
    active: Mapped[bool] = mapped_column(default=True)
    builtin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Profile(Base):
    """Profil d'essai (docs/17) : « Mon domaine », filtres et sources des Actualités.

    Le profil principal est celui de Kevin ; les autres sont fictifs, pour juger si les
    Actualités et les Formations conviennent à d'autres chercheurs d'emploi.
    """

    __tablename__ = "profiles"

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

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("news_sources.id", ondelete="CASCADE"), primary_key=True
    )
    active: Mapped[bool] = mapped_column(default=True)
