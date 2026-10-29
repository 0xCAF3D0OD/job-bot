"""Les sauvegardes (docs/82) : la base et les fichiers déposés, dans un seul fichier chiffré.

Une sauvegarde est faite avec l'accès propriétaire (`JOBBOT_MIGRATE_DATABASE_URL`), le seul qui
voit tous les comptes, sur un instantané de la base : les lignes comptées et la copie faite par
`pg_dump` sont exactement les mêmes. Le fichier :

    JOBA1SV1 | sel (16 o) | nonce (12 o) | AES-256-GCM( tar.gz )

La clé vient de la phrase secrète (`JOBBOT_BACKUP_PASSPHRASE`) par scrypt. L'archive contient
`manifeste.json` (date, migration, lignes par table, nombre de fichiers), `base.dump` (format
personnalisé de `pg_dump`) et `fichiers/…` (le stockage, sans les logos ni les miniatures des
actualités, qui se retéléchargent).
"""

import hashlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

import psycopg
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from psycopg import sql
from sqlalchemy.engine import make_url

from jobbot.db.base import APP_ROLE
from jobbot.settings import Settings, libpq

MAGIC = b"JOBA1SV1"
SUFFIX = ".jobA1backup"
NAME = re.compile(r"^jobA1-(\d{4}-\d{2}-\d{2}-\d{4})(?:-[a-z-]+)?" + re.escape(SUFFIX) + "$")
# Se retéléchargent tout seuls : inutile de les garder (docs/exploitation.md).
EXCLUDED = ("logos/", "news/")
KEEP_DAYS, KEEP_WEEKS, KEEP_MONTHS = 7, 4, 6
_SCRYPT = {"n": 2**15, "r": 8, "p": 1, "maxmem": 64 * 1024 * 1024, "dklen": 32}


class BackupError(Exception):
    """Sauvegarde ou restauration impossible ; le message est pour l'écran, sans secret."""


@dataclass(frozen=True)
class Archive:
    manifest: dict[str, Any]
    dump: bytes
    files: dict[str, bytes]


@dataclass(frozen=True)
class Saved:
    path: Path
    at: datetime
    size: int


# --- Chiffrement -----------------------------------------------------------------------------


def _key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.scrypt(passphrase.encode(), salt=salt, **_SCRYPT)


def encrypt(data: bytes, passphrase: str) -> bytes:
    salt, nonce = os.urandom(16), os.urandom(12)
    return MAGIC + salt + nonce + AESGCM(_key(passphrase, salt)).encrypt(nonce, data, MAGIC)


def decrypt(blob: bytes, passphrase: str) -> bytes:
    if not blob.startswith(MAGIC) or len(blob) < len(MAGIC) + 28:
        raise BackupError("ce fichier n'est pas une sauvegarde de jobA1")
    salt, nonce = blob[8:24], blob[24:36]
    try:
        return AESGCM(_key(passphrase, salt)).decrypt(nonce, blob[36:], MAGIC)
    except InvalidTag:
        raise BackupError("phrase secrète incorrecte, ou fichier abîmé") from None


def _passphrase(settings: Settings) -> str:
    if not settings.backup_configured or settings.backup_passphrase is None:
        raise BackupError("pas de phrase secrète : JOBBOT_BACKUP_PASSPHRASE dans .env (docs/82)")
    return settings.backup_passphrase.get_secret_value()


# --- PostgreSQL ------------------------------------------------------------------------------


def _tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise BackupError(f"{name} introuvable : installer les outils de PostgreSQL")
    return found


def _environment(url: str, database: str | None = None) -> dict[str, str]:
    """L'adresse de la base passe par l'environnement de `pg_dump`, jamais par sa ligne de
    commande : le mot de passe n'apparaît pas dans la liste des processus."""
    parsed = make_url(url)
    env = dict(os.environ)
    for key, value in (
        ("PGHOST", parsed.host),
        ("PGPORT", str(parsed.port) if parsed.port else None),
        ("PGUSER", parsed.username),
        ("PGPASSWORD", parsed.password),
        ("PGDATABASE", database or parsed.database),
    ):
        if value:
            env[key] = str(value)
    return env


def _connect(settings: Settings, *, autocommit: bool = False) -> psycopg.Connection[Any]:
    return psycopg.connect(libpq(settings.url_for("admin")), autocommit=autocommit)


def _sees_everything(conn: psycopg.Connection[Any]) -> bool:
    """Superutilisateur, BYPASSRLS ou propriétaire des tables : seul cet accès voit tous les
    comptes. Avec le rôle de l'API, la sauvegarde serait incomplète sans le dire."""
    row = conn.execute(
        "select r.rolsuper or r.rolbypassrls or r.rolname = "
        "(select tableowner from pg_tables where schemaname = 'public' and tablename = 'offers') "
        "from pg_roles r where r.rolname = current_user"
    ).fetchone()
    return bool(row and row[0])


def _tables(conn: psycopg.Connection[Any]) -> list[str]:
    rows = conn.execute(
        "select tablename from pg_tables where schemaname = 'public' order by tablename"
    ).fetchall()
    return [str(r[0]) for r in rows]


def _counts(conn: psycopg.Connection[Any]) -> dict[str, int]:
    found = {}
    for table in _tables(conn):
        row = conn.execute(sql.SQL("select count(*) from {}").format(sql.Identifier(table)))
        found[table] = int(row.fetchone()[0])  # type: ignore[index]
    return found


def _dump(settings: Settings) -> tuple[bytes, dict[str, int], str | None]:
    url = settings.url_for("admin")
    with _connect(settings) as conn:
        if not _sees_everything(conn):
            raise BackupError(
                "la sauvegarde demande l'accès propriétaire : JOBBOT_MIGRATE_DATABASE_URL (docs/82)"
            )
        conn.rollback()
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        conn.read_only = True
        with conn.transaction():
            snapshot = conn.execute("select pg_export_snapshot()").fetchone()[0]  # type: ignore[index]
            counts = _counts(conn)
            revision_row = conn.execute("select version_num from alembic_version").fetchone()
            done = subprocess.run(
                [_tool("pg_dump"), "--format=custom", f"--snapshot={snapshot}"],
                env=_environment(url),
                capture_output=True,
                check=False,
            )
    if done.returncode != 0:
        raise BackupError(f"pg_dump a échoué : {done.stderr.decode(errors='replace')[:300]}")
    return done.stdout, counts, str(revision_row[0]) if revision_row else None


# --- Archive ---------------------------------------------------------------------------------


def _stored_files(settings: Settings) -> dict[str, bytes]:
    root = settings.storage_path.resolve()
    files: dict[str, bytes] = {}
    if not root.exists():
        return files
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(EXCLUDED):
            continue
        files[relative] = path.read_bytes()
    return files


def _tar(manifest: dict[str, Any], dump: bytes, files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:

        def add(name: str, data: bytes) -> None:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(data))

        add("manifeste.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode())
        add("base.dump", dump)
        for name, data in files.items():
            add(f"fichiers/{name}", data)
    return buffer.getvalue()


def _safe(name: str) -> str | None:
    """Un nom d'archive sans `..` ni chemin absolu : jamais d'écriture hors du stockage."""
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not name.startswith("fichiers/"):
        return None
    return str(PurePosixPath(*path.parts[1:]))


def open_backup(path: Path, passphrase: str) -> Archive:
    data = decrypt(path.read_bytes(), passphrase)
    manifest: dict[str, Any] = {}
    dump = b""
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            content = archive.extractfile(member)
            body = content.read() if content else b""
            if member.name == "manifeste.json":
                manifest = json.loads(body)
            elif member.name == "base.dump":
                dump = body
            elif (name := _safe(member.name)) is not None:
                files[name] = body
    if not manifest or not dump:
        raise BackupError("sauvegarde incomplète : manifeste ou base absents")
    return Archive(manifest, dump, files)


def make_backup(
    settings: Settings, *, label: str | None = None, now: datetime | None = None
) -> Saved:
    """Une sauvegarde complète, écrite dans `JOBBOT_BACKUP_PATH`."""
    passphrase = _passphrase(settings)
    moment = now or datetime.now(UTC)
    dump, counts, revision = _dump(settings)
    files = _stored_files(settings)
    manifest = {
        "format": 1,
        "created_at": moment.isoformat(),
        "version": settings.version,
        "revision": revision,
        "tables": counts,
        "files": len(files),
    }
    blob = encrypt(_tar(manifest, dump, files), passphrase)
    folder = settings.backup_path
    folder.mkdir(parents=True, exist_ok=True)
    name = f"jobA1-{moment.strftime('%Y-%m-%d-%H%M')}{f'-{label}' if label else ''}{SUFFIX}"
    target = folder / name
    temporary = folder / f".{name}.partiel"
    temporary.write_bytes(blob)
    temporary.chmod(0o600)
    temporary.replace(target)
    return Saved(target, moment, len(blob))


# --- Ce qui est gardé ------------------------------------------------------------------------


def saved(settings: Settings) -> list[Saved]:
    """Les sauvegardes du dossier, la plus récente d'abord."""
    folder = settings.backup_path
    found = []
    if folder.exists():
        for path in folder.iterdir():
            if match := NAME.match(path.name):
                at = datetime.strptime(match.group(1), "%Y-%m-%d-%H%M").replace(tzinfo=UTC)
                found.append(Saved(path, at, path.stat().st_size))
    return sorted(found, key=lambda s: s.at, reverse=True)


def to_keep(dates: list[datetime], now: datetime) -> set[datetime]:
    """Les 7 derniers jours ; puis la plus récente de chaque semaine sur 4 semaines, et de
    chaque mois sur 6 mois. La plus récente de toutes est toujours gardée."""
    keep = set(sorted(dates, reverse=True)[:1])
    weeks: dict[tuple[int, int], datetime] = {}
    months: dict[tuple[int, int], datetime] = {}
    for at in dates:
        age = now - at
        if age <= timedelta(days=KEEP_DAYS):
            keep.add(at)
        if age <= timedelta(weeks=KEEP_WEEKS):
            week = at.isocalendar()[:2]
            weeks[week] = max(weeks.get(week, at), at)
        if age <= timedelta(days=31 * KEEP_MONTHS):
            months[(at.year, at.month)] = max(months.get((at.year, at.month), at), at)
    return keep | set(weeks.values()) | set(months.values())


def prune(settings: Settings, now: datetime | None = None) -> list[Path]:
    present = saved(settings)
    keep = to_keep([s.at for s in present], now or datetime.now(UTC))
    removed = []
    for item in present:
        if item.at not in keep:
            item.path.unlink(missing_ok=True)
            removed.append(item.path)
    return removed


# --- Restauration ----------------------------------------------------------------------------


def _restore_into(settings: Settings, database: str, dump: bytes) -> None:
    """Les règles de droits par défaut (`ALTER DEFAULT PRIVILEGES FOR ROLE …`) nomment le
    propriétaire de la base d'origine (sur un Mac, l'utilisateur du Mac) : elles sont laissées
    de côté, puis reposées au nom de celui qui restaure (`_default_privileges`)."""
    env = _environment(settings.url_for("admin"), database)
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder) / "base.dump"
        archive.write_bytes(dump)
        listed = subprocess.run(
            [_tool("pg_restore"), "--list", str(archive)],
            env=env,
            capture_output=True,
            check=False,
        )
        if listed.returncode != 0:
            raise BackupError(
                f"pg_restore a échoué : {listed.stderr.decode(errors='replace')[:300]}"
            )
        kept = Path(folder) / "liste"
        kept.write_text(
            "".join(
                line
                for line in listed.stdout.decode().splitlines(keepends=True)
                if " DEFAULT ACL " not in line
            )
        )
        done = subprocess.run(
            [
                _tool("pg_restore"),
                "--no-owner",
                "--exit-on-error",
                "--single-transaction",
                "--use-list",
                str(kept),
                "--dbname",
                database,
                str(archive),
            ],
            env=env,
            capture_output=True,
            check=False,
        )
    if done.returncode != 0:
        raise BackupError(f"pg_restore a échoué : {done.stderr.decode(errors='replace')[:300]}")


def _default_privileges(conn: psycopg.Connection[Any]) -> None:
    """Les droits que l'API recevra sur les tables créées par les prochaines migrations, comme
    les pose la migration 0054, au nom du propriétaire d'ici."""
    conn.execute(
        f"alter default privileges in schema public "
        f"grant select, insert, update, delete on tables to {APP_ROLE}"
    )
    conn.execute(
        f"alter default privileges in schema public grant usage, select on sequences to {APP_ROLE}"
    )


def restore_test(settings: Settings, path: Path) -> dict[str, int]:
    """Restaure dans une base à part, compte, puis efface la base : rien n'est touché."""
    archive = open_backup(path, _passphrase(settings))
    database = f"jobbot_essai_{secrets.token_hex(4)}"
    with _connect(settings, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(database)))
    try:
        _restore_into(settings, database, archive.dump)
        # render_as_string(hide_password=False) : str() remplacerait le mot de passe par « *** »
        # et la connexion échouerait sur une base protégée par mot de passe.
        url = (
            make_url(settings.url_for("admin"))
            .set(database=database)
            .render_as_string(hide_password=False)
        )
        with psycopg.connect(libpq(url)) as conn:
            counts = _counts(conn)
    finally:
        with _connect(settings, autocommit=True) as admin:
            admin.execute(
                sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(database))
            )
    expected = {k: int(v) for k, v in archive.manifest["tables"].items()}
    if counts != expected:
        differ = sorted(t for t in set(counts) | set(expected) if counts.get(t) != expected.get(t))
        raise BackupError(f"restauration incomplète : tables {', '.join(differ[:5])}")
    if len(archive.files) != int(archive.manifest["files"]):
        raise BackupError("restauration incomplète : fichiers manquants")
    return {"tables": len(counts), "rows": sum(counts.values()), "files": len(archive.files)}


def restore(settings: Settings, path: Path) -> Archive:
    """Remet la base et les fichiers de la sauvegarde. La base est vidée puis remplie : à faire
    après un essai réussi (`restore_test`), pendant une maintenance."""
    archive = open_backup(path, _passphrase(settings))
    database = make_url(settings.url_for("admin")).database or ""
    with _connect(settings, autocommit=True) as admin:
        if not _sees_everything(admin):
            raise BackupError("la restauration demande l'accès propriétaire (docs/82)")
        admin.execute("drop schema public cascade")
        admin.execute("create schema public")
    _restore_into(settings, database, archive.dump)
    with _connect(settings, autocommit=True) as admin:
        _default_privileges(admin)
    root = settings.storage_path.resolve()
    for name, data in archive.files.items():
        target = (root / name).resolve()
        if root not in target.parents:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return archive


# --- État, gardé dans les réglages de l'installation -----------------------------------------

STATUS_KEY = "backup"
# Au-delà, « La plateforme » le dit en rouge et une alerte part sur le téléphone (docs/82 §1).
LATE_AFTER = timedelta(hours=36)


def late(status: dict[str, Any], now: datetime) -> bool:
    """La dernière sauvegarde réussie date de plus de 36 heures, ou la dernière a échoué."""
    last = _when(status.get("last_at"))
    failed = _when(status.get("error_at"))
    if failed and (last is None or failed > last):
        return True
    return last is None or now - last > LATE_AFTER


def _when(value: object) -> datetime | None:
    return datetime.fromisoformat(value) if isinstance(value, str) else None
