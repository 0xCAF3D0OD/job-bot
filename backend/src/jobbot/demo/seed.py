"""Remplit une base de démo (docs/72 §4) : `jobbot demo-seed`.

Vide d'abord la base (comptes, et avec eux toutes leurs données ; actualités), puis crée
l'exploitant inerte et le compte fictif « demo », et le remplit au nom de ce compte à partir
de `demo/data.py`. Les dates suivent le jour du remplissage : relancée chaque nuit, la démo
a toujours l'air d'être « cette semaine ». Refuse une base qui contient un vrai compte.
"""

import hashlib
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts, demo
from jobbot.certificates import service as certificates
from jobbot.core.filter import ContractType, Criteria
from jobbot.core.orp import LOCAL_TZ, shift_month
from jobbot.db.models import (
    AlertSearch,
    AlertSetup,
    Application,
    Contact,
    Document,
    Draft,
    Evaluation,
    Interview,
    JobRun,
    NewsItem,
    NewsSource,
    Notification,
    Offer,
    OfferLink,
    OfferSighting,
    OrpMeeting,
    OrpMonth,
    Profile,
    ProfileChunk,
    ProfileSource,
    Search,
    Setting,
    Training,
    TrainingMark,
    User,
)
from jobbot.demo import data
from jobbot.filtering.service import run_filter, save_criteria
from jobbot.followups.service import local_today
from jobbot.llm.scoring import PROMPT_VERSION, profile_hash
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile
from jobbot.trainings.service import sync_catalog

MODEL = "démo"
LINKS = "https://emplois.exemple.ch"


def _at(day: date, hour: int = 8, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), LOCAL_TZ)


def _month_start(today: date, offset: int) -> date:
    year, month = (int(x) for x in shift_month(f"{today:%Y-%m}", -offset).split("-"))
    return date(year, month, 1)


def sent_day(today: date, offset: int, fraction: float) -> date:
    """Un jour du mois (0 : en cours, jusqu'à hier ; 1 : le précédent…), à cette fraction."""
    first = _month_start(today, offset)
    if offset == 0:
        last = max(first, today - timedelta(days=1))
    else:
        last = _month_start(today, offset - 1) - timedelta(days=1)
    return first + timedelta(days=round((last - first).days * fraction))


def next_thursday(today: date) -> date:
    ahead = (3 - today.weekday()) % 7 or 7
    return today + timedelta(days=ahead)


def _address(spec: data.OfferSpec, number: int) -> str:
    return f"Rue de l'Exemple {number}, {data.CITIES[spec.city]} {spec.city}"


async def _wipe_and_create_accounts(session: AsyncSession) -> int:
    # Les données d'un compte partent avec lui (clés étrangères en cascade).
    await session.execute(delete(User))
    await session.execute(delete(JobRun))
    await session.execute(delete(NewsItem))
    await session.execute(delete(NewsSource))
    session.add(
        User(username=accounts.PLACEHOLDER_USERNAME, password_hash=accounts.UNUSABLE_PASSWORD)
    )
    await session.flush()
    visitor = User(username=demo.DEMO_USERNAME, password_hash=accounts.UNUSABLE_PASSWORD)
    session.add(visitor)
    await session.flush()
    return visitor.id


async def _profile(session: AsyncSession) -> tuple[Profile, dict[str, int]]:
    for key, value in {
        **data.IDENTITY,
        "orp_monthly_target": data.ORP_TARGET,
        "welcome": {"done": True, "trade": data.TRADE},
    }.items():
        session.add(Setting(key=key, value=value))
    await save_criteria(
        session,
        Criteria(
            locations=data.LOCATIONS,
            min_rate=data.MIN_RATE,
            excluded_types=tuple(ContractType(v) for v in data.EXCLUDED_TYPES),
        ),
    )
    profile = Profile(
        name="Profil principal",
        is_main=True,
        occupation=data.OCCUPATION,
        preferences={"domain_keywords": data.DOMAIN_KEYWORDS, "domain_only": False},
    )
    session.add(profile)
    chunks = {}
    for chunk in data.CHUNKS:
        row = ProfileChunk(
            kind=chunk.kind, title=chunk.title, content=chunk.content, tags=list(chunk.tags)
        )
        session.add(row)
        await session.flush()
        chunks[chunk.key] = row.id
    return profile, chunks


def _first_seen(spec: data.OfferSpec, today: date) -> date:
    if spec.applied is not None:
        return sent_day(today, spec.applied.month, spec.applied.fraction) - timedelta(days=2)
    return today - timedelta(days=spec.days_ago)


async def _search(
    session: AsyncSession, cache: dict[tuple[str, date], Search], source: str, day: date
) -> Search:
    found = cache.get((source, day))
    if found is None:
        found = Search(
            source=source,
            message_id=f"demo-{source}-{day.isoformat()}",
            received_at=_at(day, 7, 30),
            subject="Nouvelles offres pour ta recherche",
            alert_label="DevOps · Suisse romande",
            raw_key="demo",
            parse_status="parsed",
            results_count=4 + day.day % 5,
            new_offers_count=1 + day.day % 3,
        )
        session.add(found)
        await session.flush()
        cache[(source, day)] = found
    return found


async def _offers(session: AsyncSession, today: date) -> dict[str, Offer]:
    # Le journal des recherches : une alerte par jour (jobup, Indeed), jobs.ch tous les trois.
    cache: dict[tuple[str, date], Search] = {}
    start = _month_start(today, 2)
    day = start
    while day <= today:
        for source in ("jobup", "indeed"):
            await _search(session, cache, source, day)
        if (day - start).days % 3 == 0:
            await _search(session, cache, "jobsch", day)
        day += timedelta(days=1)

    offers = {}
    for number, spec in enumerate(data.OFFERS, start=1):
        seen = _first_seen(spec, today)
        offer = Offer(
            fingerprint=f"demo-{spec.key}",
            title=spec.title,
            company=spec.company,
            location=f"{spec.city}, {data.CANTONS[spec.city]}",
            rate_min=spec.rate[0],
            rate_max=spec.rate[1],
            snippet=f"{spec.title} chez {spec.company}. {spec.extra}".strip(),
            description=(
                f"{spec.company} cherche un·e {spec.title} pour son équipe à {spec.city}. "
                f"Vous travaillez avec {', '.join(spec.asks)}. {spec.contract}, "
                f"{spec.rate[0]}-{spec.rate[1]} %. Offre fictive de la démo jobA1."
            ),
            employment_type=spec.contract,
            # Toutes passent d'abord par le filtre (« new ») ; leur état vient ensuite.
            status="new",
            first_seen_at=_at(seen, 7, 30),
            last_seen_at=_at(seen, 7, 30),
            seen_since=_at(seen, 7, 30),
            apply_url=f"{LINKS}/postuler/{number}",
            apply_kind="external",
            enrich_status="ok",
            enriched_at=_at(seen, 8),
            company_address=_address(spec, number),
            company_address_source="page",
            company_website="https://www.exemple.ch",
        )
        session.add(offer)
        await session.flush()
        session.add(
            OfferLink(
                offer_id=offer.id,
                source=spec.source,
                external_id=spec.key,
                url=f"{LINKS}/offres/{number}",
            )
        )
        if spec.source in ("jobup", "indeed", "jobsch"):
            day = seen
            while (spec.source, day) not in cache and day < today:
                day += timedelta(days=1)
            if (spec.source, day) in cache:
                session.add(
                    OfferSighting(
                        offer_id=offer.id,
                        search_id=cache[(spec.source, day)].id,
                        position=1,
                        is_first=True,
                    )
                )
        offers[spec.key] = offer
    return offers


def _and(items: list[str]) -> str:
    """« Azure, Terraform et réseau »."""
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} et {items[-1]}"


def _evaluation(spec: data.OfferSpec, chunks: dict[str, int], seen: datetime) -> dict[str, Any]:
    remote = {"hybrid": "2 jours de télétravail", "onsite": "sur place", "full": "télétravail"}
    covered = [a for a in spec.asks if a not in spec.missing]
    strengths: list[dict[str, Any]]
    if spec.role:
        strengths = [
            {
                "text": "Automatisation : scripts en Bash et Python.",
                "chunk_ids": [chunks["exp_support"]],
            }
        ]
    else:
        strengths = [
            {
                "text": "Kubernetes : plateforme de 40 services en production.",
                "chunk_ids": [chunks["exp_platform"], chunks["comp_k8s"]],
            },
            {
                "text": "Terraform : infrastructure sur Azure et AWS.",
                "chunk_ids": [chunks["comp_iac"], chunks["exp_cloud"]],
            },
        ]
    if spec.score is not None and spec.score >= 80:
        strengths.append(
            {
                "text": "Supervision : astreintes avec Prometheus et Grafana.",
                "chunk_ids": [chunks["comp_obs"]],
            }
        )
    gaps: list[dict[str, Any]] = [
        {"text": f"{m} : demandé, absent de ton profil.", "chunk_ids": []} for m in spec.missing
    ]
    # Une note basse sans compétence manquante : le poste penche vers le développement.
    far_from_dev = spec.score is not None and spec.score < 70 and not spec.role and not spec.missing
    if spec.role:
        gaps.append(
            {
                "text": "Domaine : le poste vise la donnée, ton parcours la plateforme.",
                "chunk_ids": [chunks["exp_platform"]],
            }
        )
    elif far_from_dev:
        gaps.append(
            {
                "text": "Développement : le poste en demande plus que ton profil.",
                "chunk_ids": [chunks["exp_platform"]],
            }
        )
    # La phrase « pourquoi » (score-v5, docs/121 §C.1) dit la même chose que les points forts
    # et les manques de l'offre : ce qu'elle demande et que le profil a, ce qui manque.
    parts = []
    if covered:
        parts.append(f"{_and(covered)} : dans ton profil")
    if spec.missing:
        parts.append(f"il manque {_and(list(spec.missing))}")
    if far_from_dev:
        parts.append("le poste demande plus de développement")
    why = spec.why or " ; ".join(parts) + "."
    return {
        "score": spec.score,
        "why": why[0].upper() + why[1:],
        "level": spec.level,
        "level_detail": spec.level_detail or None,
        "summary_role": f"{spec.title} chez {spec.company}, à {spec.city} : "
        + (spec.role or "faire tourner et améliorer la plateforme de l'entreprise."),
        "summary_asks": f"Expérience de {', '.join(spec.asks)} ; français courant, anglais "
        "technique.",
        "summary_offers": f"{spec.rate[0]}-{spec.rate[1]} %, {remote[spec.remote]}, "
        f"{spec.contract}.",
        "summary_partial": False,
        "strengths": strengths,
        "gaps": gaps,
        "keywords_role": ["Données"] if spec.role else ["Plateforme", "Cloud"],
        "keywords_asks": [{"text": a, "covered": a in covered} for a in spec.asks],
        "keywords_offers": [
            f"{spec.rate[1]} %",
            "Hybride" if spec.remote == "hybrid" else "Sur place",
        ],
        "remote": spec.remote,
        "remote_days": 2 if spec.remote == "hybrid" else None,
        "remote_region": None,
        "remote_from_switzerland": None,
        "scam_signals": [],
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "scored_at": seen + timedelta(hours=1),
        "notified_at": seen + timedelta(hours=1),
    }


async def _scores(session: AsyncSession, offers: dict[str, Offer], chunks: dict[str, int]) -> None:
    current = profile_hash(await active_profile(session))
    for spec in data.OFFERS:
        if spec.score is None:
            continue
        offer = offers[spec.key]
        values = _evaluation(spec, chunks, offer.first_seen_at)
        await session.execute(
            update(Evaluation)
            .where(Evaluation.offer_id == offer.id)
            .values(**values, profile_hash=current)
        )


def _letter(
    spec: data.OfferSpec, chunks: dict[str, int], address: str, contact: str | None
) -> dict[str, Any]:
    return {
        "subject": f"Candidature au poste de {spec.title}",
        "paragraphs": [
            {
                "text": f"Votre annonce pour un poste de {spec.title} chez {spec.company} a "
                "retenu toute mon attention : construire et faire vivre une plateforme fiable "
                "est exactement ce que je fais depuis cinq ans.",
                "chunk_ids": [],
            },
            {
                "text": "Chez mon employeur actuel, j'ai mis en place une plateforme Kubernetes "
                "pour une quarantaine de services, avec des déploiements continus qui ont "
                "ramené la mise en production de deux jours à vingt minutes.",
                "chunk_ids": [chunks["exp_platform"]],
            },
            {
                "text": "J'ai aussi conduit la migration de notre infrastructure vers le cloud, "
                "décrite entièrement en Terraform, et organisé la supervision et les "
                "astreintes de l'équipe.",
                "chunk_ids": [chunks["exp_cloud"], chunks["comp_obs"]],
            },
            {
                "text": "Je serais heureux·se d'en parler avec vous lors d'un entretien.",
                "chunk_ids": [],
            },
        ],
        "employer": {"address": address, "contact_name": contact, "contact_phone": None},
    }


def _cv(spec: data.OfferSpec, chunks: dict[str, int]) -> dict[str, Any]:
    order = ["exp_platform", "exp_cloud", "exp_support", "comp_k8s", "comp_iac", "comp_obs"]
    return {
        "headline": spec.title,
        "summary": "Ingénieur·e DevOps avec cinq ans d'expérience des plateformes Kubernetes et "
        "du cloud : déploiements continus, infrastructure as code, supervision et astreintes.",
        "chunk_ids": [chunks[k] for k in [*order, "formation", "langues"]],
        "keywords": [a for a in spec.asks if a not in spec.missing],
    }


async def _drafts(
    session: AsyncSession, offer: Offer, spec: data.OfferSpec, chunks: dict[str, int]
) -> tuple[int, int]:
    contact = spec.applied.contact if spec.applied else None
    letter = Draft(
        offer_id=offer.id,
        kind="letter",
        version=1,
        language="fr",
        content=_letter(spec, chunks, offer.company_address or "", contact),
        model=MODEL,
        prompt_version="demo",
    )
    cv = Draft(
        offer_id=offer.id,
        kind="cv",
        version=1,
        language="fr",
        content=_cv(spec, chunks),
        model=MODEL,
        prompt_version="demo",
    )
    session.add_all([letter, cv])
    await session.flush()
    return letter.id, cv.id


async def _applications(
    session: AsyncSession, offers: dict[str, Offer], chunks: dict[str, int], today: date
) -> int:
    count = 0
    current = f"{today:%Y-%m}"
    # Une lettre et un CV déjà rédigés pour les deux meilleures offres à examiner : la démo ne
    # rédige rien (pas d'IA), le visiteur voit quand même la fonction phare (docs/126 §5).
    showcase = {
        s.key
        for s in sorted(
            (s for s in data.OFFERS if s.applied is None and s.state == "to_review" and s.score),
            key=lambda s: s.score or 0,
            reverse=True,
        )[:2]
    }
    for spec in data.OFFERS:
        offer = offers[spec.key]
        if spec.applied is None:
            if spec.state == "preparing" or spec.key in showcase:
                await _drafts(session, offer, spec, chunks)
            continue
        applied = spec.applied
        sent = sent_day(today, applied.month, applied.fraction)
        month = f"{sent:%Y-%m}"
        letter_id = cv_id = None
        if applied.letter:
            letter_id, cv_id = await _drafts(session, offer, spec, chunks)
        status_at = None
        if applied.status in ("refus", "sans_reponse", "entretien"):
            status_at = min(today, sent + timedelta(days=12))
        interview_at = None
        if applied.interview == "upcoming":
            interview_at = _at(next_thursday(today), 10)
        elif applied.interview in ("held", "refused"):
            interview_at = _at(min(today - timedelta(days=1), sent + timedelta(days=10)), 14)
        # Les mois passés sont déclarés dans Job-Room ; le mois en cours, en partie.
        declared = None
        if month != current:
            declared = _month_start(today, applied.month - 1) + timedelta(days=2)
        elif applied.fraction < 0.4:
            declared = sent + timedelta(days=1)
        application = Application(
            offer_id=offer.id,
            sent_at=sent,
            method=applied.method,
            company=spec.company,
            company_address=offer.company_address,
            contact_name=applied.contact,
            job_title=spec.title,
            location=spec.city,
            rate_text="plein temps"
            if spec.rate[1] == 100 and spec.rate[0] == 100
            else f"temps partiel ({spec.rate[0]}-{spec.rate[1]} %)",
            application_url=offer.apply_url,
            status=applied.status,
            status_reason=applied.reason,
            status_at=status_at,
            followed_up_at=sent + timedelta(days=14) if applied.followed_up else None,
            interview_at=interview_at,
            orp_month=month,
            job_room_at=min(declared, today) if declared else None,
            letter_draft_id=letter_id,
            cv_draft_id=cv_id,
        )
        session.add(application)
        await session.flush()
        count += 1
        if applied.interview in ("held", "refused"):
            values = data.INTERVIEW_HELD if applied.interview == "held" else data.INTERVIEW_REFUSED
            held = interview_at.date() if interview_at else sent
            session.add(
                Interview(
                    application_id=application.id,
                    held_at=held,
                    next_step_at=today + timedelta(days=5) if applied.interview == "held" else None,
                    **values,
                )
            )
        if applied.contact:
            session.add(
                Contact(
                    offer_id=offer.id,
                    application_id=application.id,
                    name=applied.contact,
                    role="recruiter",
                    channel="linkedin_message",
                    contacted_on=sent - timedelta(days=1),
                    answered_on=sent + timedelta(days=2),
                    note="Échange cordial, conseille de mettre en avant les astreintes.",
                )
            )
    for number, (offset, fraction, company, title, city, status) in enumerate(
        data.MANUAL_APPLICATIONS, start=100
    ):
        sent = sent_day(today, offset, fraction)
        session.add(
            Application(
                sent_at=sent,
                method="electronique",
                company=company,
                company_address=f"Rue de l'Exemple {number}, {data.CITIES[city]} {city}",
                job_title=title,
                location=city,
                rate_text="plein temps",
                application_url=f"{LINKS}/postuler/{number}",
                status=status,
                status_at=min(today, sent + timedelta(days=15)),
                orp_month=f"{sent:%Y-%m}",
                job_room_at=_month_start(today, offset - 1) + timedelta(days=2),
            )
        )
        count += 1
    # Remise des preuves : les mois passés sont remis le 3 du mois suivant.
    for offset in (3, 2, 1):
        month = f"{_month_start(today, offset):%Y-%m}"
        handed = _month_start(today, offset - 1) + timedelta(days=2)
        if handed < today:
            session.add(
                OrpMonth(
                    month=month,
                    submitted_at=_at(handed, 18),
                    exported_at=_at(handed, 17),
                    reminders_sent={},
                )
            )
    return count


async def _around(session: AsyncSession, profile: Profile, today: date) -> None:
    # Le prochain rendez-vous ORP, la semaine prochaine (docs/83) : sa feuille est prête.
    session.add(
        OrpMeeting(
            # Un mardi, au moins cinq jours plus tard : jamais un week-end.
            starts_at=_at(
                today + timedelta(days=5 + (1 - (today + timedelta(days=5)).weekday()) % 7), 9, 30
            ),
            place="ORP de Lausanne",
            questions=[
                {
                    "key": "custom:1",
                    "text": "Puis-je suivre un cours d'allemand pendant ma recherche ?",
                    "checked": True,
                }
            ],
        )
    )
    # Le précédent, il y a cinq semaines : ce qui a été convenu, dans le carnet.
    previous = today - timedelta(days=35)
    session.add(
        OrpMeeting(
            starts_at=_at(previous - timedelta(days=(previous.weekday() - 1) % 7), 10, 0),
            place="ORP de Lausanne",
            questions=[
                {
                    "key": "measure",
                    "text": "Une mesure est-elle possible (stage, cours, programme d'emploi "
                    "temporaire) ?",
                    "checked": True,
                }
            ],
            outcome_at=_at(previous, 12, 0),
            agreed_target=data.ORP_TARGET,
            measures=[{"text": "Atelier « Valoriser son CV »", "training_id": None}],
            assignments="Une assignation à suivre, reçue par courrier.",
            note="Le conseiller propose de viser aussi les postes en anglais.",
        )
    )
    # La dernière collecte : ce matin (la démo n'en lance aucune).
    session.add(
        JobRun(
            job="collect",
            started_at=_at(today, 7, 30),
            finished_at=_at(today, 7, 31),
            status="success",
            items_in=3,
            items_out=2,
        )
    )
    session.add_all(
        [
            Notification(
                kind="offers",
                title="3 nouvelles offres au-dessus de 75",
                message="Senior Platform Engineer chez Démo Data SA (87) et deux autres.",
                link="/candidatures/offres",
                created_at=_at(today, 7, 45),
            ),
            Notification(
                kind="follow_up",
                title="Relancer Maquette Médias Sàrl ?",
                message="Candidature envoyée il y a plus de deux semaines, sans réponse.",
                link="/candidatures/suivi",
                created_at=_at(today - timedelta(days=1), 9),
            ),
        ]
    )
    devops = AlertSearch(terms="DevOps", location="Lausanne")
    platform = AlertSearch(terms="Platform Engineer", location="Genève")
    session.add_all([devops, platform])
    await session.flush()
    for site in ("jobup", "indeed", "jobsch"):
        session.add(AlertSetup(search_id=devops.id, site=site))
    session.add(AlertSetup(search_id=platform.id, site="jobup"))

    # Formations : le catalogue du dépôt, deux suivies.
    await sync_catalog(session)
    trainings = list(await session.scalars(select(Training).where(Training.origin == "catalog")))
    picked = [t for t in trainings if "Kubernetes" in (t.tags or [])][:1]
    picked += [t for t in trainings if t not in picked and "Terraform" in (t.tags or [])][:1]
    for training, status in zip(picked, ("in_progress", "interested"), strict=False):
        session.add(
            TrainingMark(
                profile_id=profile.id,
                training_id=training.id,
                status=status,
                progress="Module 3 sur 6" if status == "in_progress" else None,
                funding_status="requested" if status == "in_progress" else None,
                funding_requested_at=today - timedelta(days=9) if status == "in_progress" else None,
            )
        )

    # Actualités : une source fictive, quelques articles d'exemple.
    source = NewsSource(
        kind="articles",
        name="Actualités d'exemple",
        url="https://github.com/0xCAF3D0OD/job-bot",
        feed_url="https://github.com/0xCAF3D0OD/job-bot#demo-feed",
        country="CH",
        language="fr",
        labour_market=True,
        fetched_at=datetime.now(UTC),
    )
    session.add(source)
    await session.flush()
    session.add(ProfileSource(profile_id=profile.id, source_id=source.id, active=True))
    for number, (title, summary) in enumerate(data.NEWS, start=1):
        session.add(
            NewsItem(
                source_id=source.id,
                title=title,
                url=f"https://github.com/0xCAF3D0OD/job-bot#demo-{number}",
                summary=summary,
                language="fr",
                published_at=_at(today - timedelta(days=number - 1), 6),
            )
        )


async def seed(runtime: Runtime, today: date | None = None) -> int:
    """Vide la base de démo et la remplit ; renvoie le nombre de candidatures fictives."""
    today = today or local_today()
    if not runtime.settings.demo:
        raise demo.NotADemoDatabase("le remplissage de la démo demande JOBBOT_DEMO=true")
    await demo.check(runtime.sessionmaker)
    async with runtime.sessionmaker.begin() as session:
        visitor = await _wipe_and_create_accounts(session)
    with accounts.use(visitor):
        async with runtime.sessionmaker.begin() as session:
            profile, chunks = await _profile(session)
            offers = await _offers(session, today)
            offer_ids = {key: offer.id for key, offer in offers.items()}
        # Le vrai filtre : les offres écartées le sont par les prérequis de Camille.
        await run_filter(runtime)
        async with runtime.sessionmaker.begin() as session:
            offers = {
                key: offer
                for key in offer_ids
                if (offer := await session.get(Offer, offer_ids[key])) is not None
            }
            for spec in data.OFFERS:
                if spec.applied is not None:
                    offers[spec.key].status = "applied"
                elif spec.state in ("preparing", "later", "ignored"):
                    offers[spec.key].status = spec.state
            await _scores(session, offers, chunks)
            count = await _applications(session, offers, chunks, today)
            profile = await session.get(Profile, profile.id) or profile
            await _around(session, profile, today)
            await _certificates(runtime, session, visitor)
    return count


# Deux certificats de travail fictifs (docs/87) : un très bon, un à faire corriger.
CERTIFICATES = (
    (
        "Certificat Prototype Fintech SA.txt",
        "Certificat de travail\n\nMadame Camille Exemple a travaillé chez Prototype Fintech SA "
        "du 1er mars 2021 au 30 juin 2025 en qualité d'ingénieure système.\n\nElle a accompli "
        "ses tâches toujours à notre plus grande satisfaction. Son comportement envers ses "
        "supérieurs et ses collègues a toujours été irréprochable.\n\nMadame Exemple nous quitte "
        "à sa demande. Nous regrettons vivement son départ, la remercions pour son engagement et "
        "lui souhaitons plein succès pour la suite.\n",
    ),
    (
        "Certificat Bac à sable SA.txt",
        "Certificat de travail\n\nMadame Camille Exemple a travaillé chez Bac à sable SA comme "
        "technicienne support de 2018 à 2020.\n\nElle s'est efforcée de mener à bien les tâches "
        "confiées, dans l'ensemble à notre satisfaction. Son comportement envers ses collègues "
        "et ses supérieurs était correct.\n",
    ),
)


async def _certificates(runtime: Runtime, session: AsyncSession, visitor: int) -> None:
    for n, (filename, body) in enumerate(CERTIFICATES):
        content = body.encode()
        key = f"accounts/{visitor}/documents/demo-certificat-{n}.txt"
        runtime.storage.put(key, content)
        document = Document(
            filename=filename,
            doc_type="txt",
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            storage_key=key,
            text_status="ok",
            extracted_text=body,
            kind=certificates.CERTIFICATE,
        )
        session.add(document)
        await session.flush()
        await certificates.save(session, document)
