"""Métriques Prometheus exposées sur /metrics (API et worker).

Le nom de chaque métrique est listé dans docs/exploitation.md.
"""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "jobbot_http_requests_total",
    "Requêtes HTTP traitées par l'API",
    ["method", "route", "status"],
)
HTTP_DURATION = Histogram(
    "jobbot_http_request_duration_seconds",
    "Durée des requêtes HTTP",
    ["method", "route"],
)
JOB_RUNS = Counter(
    "jobbot_job_runs_total",
    "Exécutions de tâches",
    ["job", "status"],
)
JOB_DURATION = Histogram(
    "jobbot_job_duration_seconds",
    "Durée des tâches",
    ["job"],
    buckets=(0.1, 0.5, 1, 5, 15, 30, 60, 120, 300, 600),
)
JOB_LAST_SUCCESS = Gauge(
    "jobbot_job_last_success_timestamp_seconds",
    "Horodatage Unix du dernier succès de chaque tâche",
    ["job"],
)
DB_UP = Gauge(
    "jobbot_db_up",
    "1 si la base a répondu au dernier contrôle, 0 sinon",
)
