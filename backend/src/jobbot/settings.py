"""Configuration : uniquement des variables d'environnement préfixées JOBBOT_.

Chaque secret accepte une variante `_FILE` (chemin d'un fichier qui contient la valeur),
pour les secrets Docker et les Secrets Kubernetes montés en fichier.
"""

import ipaddress
import os
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "JOBBOT_"

# Variables dont la valeur peut être lue depuis un fichier (JOBBOT_<NOM>_FILE).
SECRET_FIELDS = (
    "database_url",
    "worker_database_url",
    "migrate_database_url",
    "imap_password",
    "anthropic_api_key",
    "ntfy_topic",
)


class Env(StrEnum):
    DEV = "dev"
    PROD = "prod"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


class StorageBackend(StrEnum):
    LOCAL = "local"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        # .env à la racine du dépôt (lancement depuis backend/) ou dans le dossier courant.
        # En production, aucun fichier : seules les variables d'environnement comptent.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr
    # Trois accès à la base (docs/78 §3.1) : l'API par `database_url` (rôle jobbot_app), le
    # worker par le sien (jobbot_worker, qui écrit aussi les tables communes), et
    # `jobbot migrate`, `demo-seed`, `set-password` par celui du propriétaire des tables. Vides :
    # `database_url`, comme avant 0.64.
    worker_database_url: SecretStr | None = None
    migrate_database_url: SecretStr | None = None
    env: Env = Env.DEV
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    worker_http_port: int = Field(default=8001, ge=1, le=65535)
    log_level: str = "INFO"
    log_format: LogFormat | None = None
    scheduler_enabled: bool = True
    storage_backend: StorageBackend = StorageBackend.LOCAL
    storage_path: Path = Path("./data")
    cors_origins: list[str] = Field(default_factory=list)
    version: str = "dev"

    # Collecte des alertes (0.2). Sans utilisateur ni mot de passe, la collecte est inactive.
    imap_host: str = "imap.gmail.com"
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_user: str = ""
    imap_password: SecretStr | None = None
    imap_folder: str = "INBOX"
    imap_backfill_days: int = Field(default=30, ge=1, le=365)
    # Adresse où arrivent les alertes (docs/65 §3) ; vide : celle de la boîte (JOBBOT_IMAP_USER).
    # Un compte invité reçoit à « boite+code@domaine », livré dans la même boîte.
    mail_address: str = ""

    # Lecture des pages d'offres jobup après la collecte (docs/05). false : désactivée.
    enrich_enabled: bool = True

    # Note et résumé des offres par l'IA (docs/06). Sans clé, aucune note.
    anthropic_api_key: SecretStr | None = None
    llm_model: str = "claude-opus-5"
    llm_effort: Literal["low", "medium", "high"] = "low"
    # Rédaction des lettres (docs/08 §6) : plus de soin que la notation.
    llm_writing_effort: Literal["low", "medium", "high"] = "medium"

    # Notifications ntfy (docs/06 §5). Sujet secret : quiconque le connaît lit les messages.
    ntfy_url: str = "https://ntfy.sh"
    ntfy_topic: SecretStr | None = None
    # Adresse de l'interface, pour le lien des notifications.
    public_url: str = "http://localhost:5173"

    # Connexion (docs/18 §1) : sans session, l'API ne sert que les Actualités.
    # false seulement pour un essai local : toutes les pages redeviennent ouvertes.
    auth_enabled: bool = True
    # Intermédiaires (reverse proxy) dont l'API croit l'en-tête X-Forwarded-For : l'adresse
    # réelle du visiteur sert à limiter les essais de connexion (docs/78 §2). « * » : tous,
    # seulement si l'API n'est joignable que par son intermédiaire (conteneur).
    trusted_proxies: str = "127.0.0.1"

    # Démo publique (docs/72) : installation à part, sans connexion, en lecture seule, sur le
    # compte fictif rempli par `jobbot demo-seed`. Jamais sur une vraie plateforme.
    demo: bool = False
    # Adresse d'une démo en ligne : « La plateforme » propose « Voir la démo » (toute installation).
    demo_url: str | None = None

    @field_validator("worker_database_url", "migrate_database_url", mode="before")
    @classmethod
    def _empty_is_unset(cls, value: object) -> object:
        # Variable laissée vide : l'adresse de l'API.
        return None if value == "" else value

    @field_validator("database_url", "worker_database_url", "migrate_database_url")
    @classmethod
    def _check_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("doit commencer par postgresql+psycopg://")
        return value

    @model_validator(mode="after")
    def _derive(self) -> "Settings":
        if self.demo and (self.llm_configured or self.imap_configured or self.ntfy_configured):
            # Une démo publique ne doit ni dépenser d'IA, ni lire une boîte, ni notifier.
            raise ValueError(
                "JOBBOT_DEMO : retirer de cette installation la clé de l'IA, la boîte e-mail "
                "et ntfy"
            )
        if not self.auth_enabled and (self.is_prod or not _loopback(self.api_host)):
            # Sans connexion, toute requête agit au nom de l'exploitant (docs/78 §2).
            raise ValueError(
                "JOBBOT_AUTH_ENABLED=false : seulement pour un essai sur son ordinateur "
                "(JOBBOT_API_HOST=127.0.0.1, JOBBOT_ENV=dev)"
            )
        self.log_level = self.log_level.upper()
        if self.log_format is None:
            self.log_format = LogFormat.JSON if self.env is Env.PROD else LogFormat.CONSOLE
        return self

    @property
    def is_prod(self) -> bool:
        return self.env is Env.PROD

    @property
    def imap_configured(self) -> bool:
        password = self.imap_password.get_secret_value() if self.imap_password else ""
        return bool(self.imap_user.strip() and password)

    @property
    def llm_configured(self) -> bool:
        key = self.anthropic_api_key.get_secret_value() if self.anthropic_api_key else ""
        return bool(key.strip())

    @property
    def ntfy_configured(self) -> bool:
        topic = self.ntfy_topic.get_secret_value() if self.ntfy_topic else ""
        return bool(topic.strip())

    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url.get_secret_value()

    def url_for(self, access: str) -> str:
        """L'adresse de la base pour l'API (`app`), le worker ou les commandes du propriétaire
        (`admin`)."""
        chosen = {"worker": self.worker_database_url, "admin": self.migrate_database_url}.get(
            access
        )
        return chosen.get_secret_value() if chosen else self.sqlalchemy_url

    @property
    def libpq_url(self) -> str:
        """URL sans le suffixe de pilote SQLAlchemy, pour psycopg et procrastinate."""
        return libpq(self.sqlalchemy_url)


def _loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def libpq(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


class ConfigError(Exception):
    """Configuration invalide : le message nomme les variables fautives."""


def _values_from_files() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in SECRET_FIELDS:
        var = f"{ENV_PREFIX}{field.upper()}_FILE"
        path = os.environ.get(var)
        if not path:
            continue
        try:
            values[field] = Path(path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ConfigError(f"{var} : impossible de lire {path} ({exc.strerror})") from exc
    return values


def load_settings() -> Settings:
    try:
        return Settings(**_values_from_files())
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = err["loc"]
            name = f"{ENV_PREFIX}{str(loc[0]).upper()}" if loc else "configuration"
            msg = "variable obligatoire absente" if err["type"] == "missing" else err["msg"]
            msg = msg.removeprefix("Value error, ")
            lines.append(f"{name} : {msg}")
        raise ConfigError("\n".join(lines)) from exc
