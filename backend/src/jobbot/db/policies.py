"""Une règle pour chaque table (docs/78 §3.2).

Chaque table de la base est rangée dans une famille ; `tests/test_policies.py` compare cette
liste à la base elle-même. Une nouvelle table qui n'y est pas rangée, ou qui n'a pas les
règles de sa famille, fait échouer les tests : on ne peut pas en oublier une.

- **Personnelles** : chaque compte ne lit et n'écrit que ses lignes (`user_id`, règle
  `account_isolation`).
- **Connexion** : un compte ne voit que sa ligne, l'exploitant voit les comptes ; un jeton ou
  un identifiant n'est reconnu que par une fonction qui ne rend que le numéro du compte.
- **Communes** : tout compte lit ; seuls le worker et l'exploitant écrivent.
- **Techniques** : ni séparation ni contenu des comptes (file des tâches, version des
  migrations).
"""

from typing import Literal

Family = Literal["personal", "connection", "shared", "technical"]

PERSONAL = (
    "account_sites",
    "alert_searches",
    "alert_setups",
    "applications",
    "calendar_tokens",
    "certificate_readings",
    "chat_actions",
    "chat_conversations",
    "chat_messages",
    "contacts",
    "criteria",
    "documents",
    "drafts",
    "evaluations",
    "extension_tokens",
    "interview_practices",
    "interviews",
    "llm_batches",
    "llm_calls",
    # Les paiements de Plus reçus (docs/125 §6).
    "payments",
    "notifications",
    "offer_links",
    "offer_sightings",
    "offers",
    "orp_meetings",
    "orp_months",
    "profile_chunks",
    "profile_sources",
    "profiles",
    "score_corrections",
    "searches",
    "settings",
    "training_marks",
)
CONNECTION = ("users", "sessions", "account_links")
# Le catalogue des formations est commun ; les suggestions faites pour un profil sont à son
# compte (règle à part, par profil).
SHARED = (
    "companies",
    "company_logos",
    "sites",
    "news_sources",
    "news_items",
    "platform_settings",
    "job_runs",
    "trainings",
)
TECHNICAL = (
    "alembic_version",
    "procrastinate_events",
    "procrastinate_jobs",
    "procrastinate_periodic_defers",
    "procrastinate_workers",
)

FAMILIES: dict[str, Family] = {
    **dict.fromkeys(PERSONAL, "personal"),
    **dict.fromkeys(CONNECTION, "connection"),
    **dict.fromkeys(SHARED, "shared"),
    **dict.fromkeys(TECHNICAL, "technical"),
}
