"""Configuration : uniquement des variables d'environnement préfixées JOBBOT_.

Chaque secret accepte une variante `_FILE` (chemin d'un fichier qui contient la valeur),
pour les secrets Docker et les Secrets Kubernetes montés en fichier.
"""

import os
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "JOBBOT_"

# Variables dont la valeur peut être lue depuis un fichier (JOBBOT_<NOM>_FILE).
SECRET_FIELDS = ("database_url", "imap_password", "anthropic_api_key", "ntfy_topic")


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

    # Lecture des pages d'offres jobup après la collecte (docs/05). false : désactivée.
    enrich_enabled: bool = True

    # Note et résumé des offres par l'IA (docs/06). Sans clé, aucune note.
    anthropic_api_key: SecretStr | None = None
    llm_model: str = "claude-opus-5"
    llm_effort: Literal["low", "medium", "high"] = "low"

    # Notifications ntfy (docs/06 §5). Sujet secret : quiconque le connaît lit les messages.
    ntfy_url: str = "https://ntfy.sh"
    ntfy_topic: SecretStr | None = None
    # Adresse de l'interface, pour le lien des notifications.
    public_url: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("doit commencer par postgresql+psycopg://")
        return value

    @model_validator(mode="after")
    def _derive(self) -> "Settings":
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

    @property
    def libpq_url(self) -> str:
        """URL sans le suffixe de pilote SQLAlchemy, pour psycopg et procrastinate."""
        return self.sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://", 1)


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
