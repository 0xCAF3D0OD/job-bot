"""Les sauvegardes (docs/82) : chiffrées, gardées 7 jours, 4 semaines et 6 mois, essayées
chaque dimanche, restaurées pendant une maintenance."""

import argparse
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import psycopg
import pytest
from sqlalchemy import create_engine, make_url, text

from jobbot import backup
from jobbot.db.schema import upgrade
from jobbot.runtime import Runtime
from jobbot.settings import Settings, libpq
from jobbot.worker.jobs import RunContext
from jobbot.worker.tasks import backup as task

from .conftest import TEST_DATABASE_URL, make_settings

SCRATCH = str(make_url(TEST_DATABASE_URL).set(database="jobbot_backup_test"))
PHRASE = "une phrase d'essai assez longue"


def _admin_execute(statement: str) -> None:
    admin = create_engine(make_url(SCRATCH).set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(statement))
    admin.dispose()


@pytest.fixture
def plateforme(tmp_path: Path) -> Iterator[Settings]:
    """Une petite plateforme à part : sa base, ses fichiers, son dossier de sauvegardes."""
    _admin_execute("drop database if exists jobbot_backup_test with (force)")
    _admin_execute("create database jobbot_backup_test")
    settings = make_settings(
        database_url=SCRATCH,
        storage_path=tmp_path / "data",
        backup_path=tmp_path / "sauvegardes",
        backup_passphrase=PHRASE,
    )
    upgrade(settings)
    with psycopg.connect(libpq(SCRATCH)) as conn:
        # Le compte de l'exploitant, créé par les migrations.
        owner = conn.execute("select min(id) from users").fetchone()[0]  # type: ignore[index]
        conn.execute(
            "insert into offers (user_id, fingerprint, title, first_seen_at, last_seen_at) "
            "values (%s, 'sauvegarde', 'Poste gardé', now(), now())",
            (owner,),
        )
    (tmp_path / "data" / "documents").mkdir(parents=True)
    (tmp_path / "data" / "documents" / "cv.pdf").write_bytes(b"%PDF-1.4 mon cv")
    (tmp_path / "data" / "logos").mkdir()
    (tmp_path / "data" / "logos" / "acme.png").write_bytes(b"logo")
    yield settings
    _admin_execute("drop database if exists jobbot_backup_test with (force)")


def _count(sql: str) -> int:
    with psycopg.connect(libpq(SCRATCH)) as conn:
        return int(conn.execute(sql).fetchone()[0])  # type: ignore[index]


def test_encryption_needs_the_phrase() -> None:
    blob = backup.encrypt(b"donnees", PHRASE)
    assert b"donnees" not in blob
    assert backup.decrypt(blob, PHRASE) == b"donnees"
    with pytest.raises(backup.BackupError, match="phrase secrète incorrecte"):
        backup.decrypt(blob, "une autre phrase")
    with pytest.raises(backup.BackupError, match="pas une sauvegarde"):
        backup.decrypt(b"n'importe quoi", PHRASE)


def test_save_try_and_restore(plateforme: Settings) -> None:
    made = backup.make_backup(plateforme)
    assert made.path.name.endswith(backup.SUFFIX) and made.path.stat().st_mode & 0o777 == 0o600
    archive = backup.open_backup(made.path, PHRASE)
    # Les logos se retéléchargent : ils ne sont pas gardés.
    assert set(archive.files) == {"documents/cv.pdf"}
    assert archive.manifest["tables"]["offers"] == 1
    tried = backup.restore_test(plateforme, made.path)
    assert tried["files"] == 1 and tried["rows"] >= 2
    assert _count("select count(*) from pg_database where datname like 'jobbot_essai_%'") == 0

    # Une erreur : l'offre effacée, le CV écrasé ; la restauration remet tout.
    with psycopg.connect(libpq(SCRATCH)) as conn:
        conn.execute("delete from offers")
    (plateforme.storage_path / "documents" / "cv.pdf").write_bytes(b"abime")
    backup.restore(plateforme, made.path)
    assert _count("select count(*) from offers") == 1
    assert (plateforme.storage_path / "documents" / "cv.pdf").read_bytes() == b"%PDF-1.4 mon cv"
    # Les règles et les droits reviennent avec la base : l'API s'y connecte comme avant.
    assert _count("select count(*) from pg_policies where policyname = 'account_isolation'") > 20
    with psycopg.connect(libpq(SCRATCH)) as conn:
        assert conn.execute(
            "select has_table_privilege('jobbot_app', 'offers', 'select')"
        ).fetchone() == (True,)


def test_refused_without_phrase_or_with_the_api_role(plateforme: Settings) -> None:
    with pytest.raises(backup.BackupError, match="JOBBOT_BACKUP_PASSPHRASE"):
        backup.make_backup(plateforme.model_copy(update={"backup_passphrase": None}))
    # Avec le rôle de l'API, la base ne montrerait pas tous les comptes : refusé, pas incomplet.
    restricted = str(make_url(SCRATCH).set(username="jobbot_app"))
    try:
        psycopg.connect(libpq(restricted), connect_timeout=3).close()
    except psycopg.OperationalError:
        pytest.skip("connexion locale en jobbot_app impossible (mot de passe exigé)")
    settings = make_settings(
        database_url=restricted,
        storage_path=plateforme.storage_path,
        backup_path=plateforme.backup_path,
        backup_passphrase=PHRASE,
    )
    with pytest.raises(backup.BackupError, match="accès propriétaire"):
        backup.make_backup(settings)


def test_what_is_kept() -> None:
    now = datetime(2026, 10, 19, 3, tzinfo=UTC)
    daily = [now - timedelta(days=d) for d in range(0, 300)]
    kept = backup.to_keep(daily, now)
    assert all(now - timedelta(days=d) in kept for d in range(8))
    # Au-delà de 7 jours : une par semaine sur 4 semaines, une par mois sur 6 mois.
    older = sorted(k for k in kept if now - k > timedelta(days=7))
    assert 4 <= len(older) <= 10
    assert all(now - k <= timedelta(days=31 * 6) for k in older)
    # Une seule sauvegarde, même très ancienne : gardée.
    assert backup.to_keep([now - timedelta(days=400)], now) == {now - timedelta(days=400)}


def test_when_to_save_test_and_warn() -> None:
    three = datetime(2026, 10, 19, 1, 17, tzinfo=UTC)  # 3 h 17 à Zurich (été)
    assert task.due({}, three)
    assert task.due({"last_at": (three - timedelta(hours=21)).isoformat()}, three)
    assert not task.due(
        {"last_at": (three - timedelta(hours=21)).isoformat()}, three + timedelta(hours=2)
    )
    # L'ordinateur dormait à 3 h : rattrapée dès que la dernière date de plus de 24 heures.
    assert task.due(
        {"last_at": (three - timedelta(hours=25)).isoformat()}, three + timedelta(hours=8)
    )
    sunday = datetime(2026, 10, 18, 10, tzinfo=UTC)
    assert task.test_due({}, sunday) and not task.test_due({}, sunday + timedelta(days=1))
    assert not task.test_due({"test_at": sunday.isoformat()}, sunday + timedelta(hours=2))
    assert backup.late({}, three)
    fresh = {"last_at": (three - timedelta(hours=10)).isoformat()}
    assert not backup.late(fresh, three)
    assert backup.late({**fresh, "error_at": three.isoformat()}, three)
    assert backup.late({"last_at": (three - timedelta(hours=37)).isoformat()}, three)


async def test_nightly_task_saves_and_warns_once(
    plateforme: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[str] = []

    async def deliver(_runtime: Runtime, message: Any, *, kind: str, link: str) -> None:
        sent.append(kind)

    monkeypatch.setattr("jobbot.notify.service.deliver", deliver)
    runtime = Runtime.create(plateforme, "admin")
    try:
        ctx = RunContext(job=task.BACKUP_JOB)
        await task.nightly_backup(runtime, ctx)
        assert len(backup.saved(plateforme)) == 1 and sent == []
        status = await task.read_status(runtime)
        assert status["last_error"] is None and status["last_file"].endswith(backup.SUFFIX)
        # Une sauvegarde qui échoue : une alerte, une seule par jour.
        broken = plateforme.model_copy(update={"backup_path": Path("/dev/null/impossible")})
        runtime.settings = broken
        await task.write_status(runtime, last_at=None)
        for _ in range(2):
            with pytest.raises(OSError):
                await task.nightly_backup(runtime, ctx)
        assert sent == ["backup_failed"]
    finally:
        await runtime.dispose()


def test_restore_asks_to_write_the_word(
    plateforme: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot import __main__ as cli

    made = backup.make_backup(plateforme)
    with psycopg.connect(libpq(SCRATCH)) as conn:
        conn.execute("delete from offers")
    monkeypatch.setattr(cli, "_settings", lambda: plateforme)
    monkeypatch.setattr("builtins.input", lambda _prompt: "oui")
    assert cli.cmd_restore(argparse.Namespace(file=str(made.path), essai=False)) == 1
    assert _count("select count(*) from offers") == 0  # rien n'est changé
    monkeypatch.setattr("builtins.input", lambda _prompt: "restaurer")
    assert cli.cmd_restore(argparse.Namespace(file=str(made.path), essai=False)) == 0
    assert _count("select count(*) from offers") == 1
    # L'état d'avant a été gardé, et la maintenance est levée.
    assert any("avant-restauration" in s.path.name for s in backup.saved(plateforme))
    assert (
        _count(
            "select count(*) from platform_settings where key = 'maintenance' "
            "and value <> 'null'::jsonb"
        )
        == 0
    )
