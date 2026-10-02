from pathlib import Path

import pytest

from jobbot.settings import ConfigError, LogFormat, load_settings


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Aucune variable JOBBOT_ ni fichier .env hérité du poste de développement."""
    import os

    for name in list(os.environ):
        if name.startswith("JOBBOT_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)


def test_missing_database_url_names_the_variable() -> None:
    with pytest.raises(ConfigError, match="JOBBOT_DATABASE_URL : variable obligatoire absente"):
        load_settings()


def test_wrong_driver_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL", "postgresql://localhost/jobbot")
    with pytest.raises(ConfigError, match="JOBBOT_DATABASE_URL : doit commencer"):
        load_settings()


def test_invalid_port_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL", "postgresql+psycopg://localhost/jobbot")
    monkeypatch.setenv("JOBBOT_API_PORT", "abc")
    with pytest.raises(ConfigError, match="JOBBOT_API_PORT"):
        load_settings()


def test_secret_read_from_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    secret = tmp_path / "db_url"
    secret.write_text("postgresql+psycopg://user:pass@db:5432/jobbot\n")
    monkeypatch.setenv("JOBBOT_DATABASE_URL_FILE", str(secret))
    settings = load_settings()
    assert settings.sqlalchemy_url == "postgresql+psycopg://user:pass@db:5432/jobbot"
    assert settings.libpq_url == "postgresql://user:pass@db:5432/jobbot"


def test_unreadable_secret_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL_FILE", str(tmp_path / "absent"))
    with pytest.raises(ConfigError, match="JOBBOT_DATABASE_URL_FILE"):
        load_settings()


def test_defaults_and_prod_log_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL", "postgresql+psycopg://localhost/jobbot")
    dev = load_settings()
    assert (dev.api_host, dev.api_port, dev.worker_http_port) == ("127.0.0.1", 8000, 8001)
    assert dev.log_format is LogFormat.CONSOLE
    assert dev.scheduler_enabled is True
    monkeypatch.setenv("JOBBOT_ENV", "prod")
    assert load_settings().log_format is LogFormat.JSON


def test_secret_is_not_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL", "postgresql+psycopg://u:motdepasse@h/db")
    assert "motdepasse" not in repr(load_settings())
