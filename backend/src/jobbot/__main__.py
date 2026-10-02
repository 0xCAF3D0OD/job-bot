"""Point d'entrée unique : `jobbot <commande>`.

api          API HTTP (permanent)
worker       file de tâches + tâches planifiées (permanent)
migrate      applique les migrations puis s'arrête
run-job NOM  exécute une tâche une fois ; code retour 0 (succès) ou 1 (échec)
check        valide la configuration et la connexion à la base
openapi      écrit le schéma OpenAPI de l'API sur la sortie standard (sans base)
imap-sample  copie les derniers e-mails de la boîte dans <stockage>/samples (lecture seule)
reparse      réanalyse les copies brutes stockées (après un analyseur nouveau ou corrigé)
anonymize-sample ID…  fait des jeux de test anonymisés à partir d'alertes stockées
"""

import argparse
import asyncio
import json
import sys

from jobbot.log import configure_logging, get_logger
from jobbot.settings import ConfigError, Settings, load_settings

EXIT_CONFIG_ERROR = 2


def _settings() -> Settings:
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Configuration invalide :\n{exc}", file=sys.stderr)
        raise SystemExit(EXIT_CONFIG_ERROR) from exc
    configure_logging(settings)
    return settings


def cmd_api(_: argparse.Namespace) -> int:
    import uvicorn

    from jobbot.api.app import create_app

    settings = _settings()
    uvicorn.run(
        create_app(settings),
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=20,
    )
    return 0


def cmd_worker(_: argparse.Namespace) -> int:
    from jobbot.worker.app import run_worker

    asyncio.run(run_worker(_settings()))
    return 0


def cmd_migrate(_: argparse.Namespace) -> int:
    from jobbot.db.schema import head_revision, upgrade

    settings = _settings()
    log = get_logger("jobbot.migrate")
    log.info("migrate_started", target=head_revision())
    upgrade(settings)
    log.info("migrate_finished", revision=head_revision())
    return 0


def cmd_run_job(args: argparse.Namespace) -> int:
    from jobbot.runtime import Runtime
    from jobbot.worker import tasks as _tasks  # noqa: F401  (enregistre les tâches)
    from jobbot.worker.jobs import JOBS, execute

    settings = _settings()
    if args.name not in JOBS:
        print(f"Tâche inconnue : {args.name}. Tâches : {', '.join(sorted(JOBS))}", file=sys.stderr)
        return 1

    async def run() -> bool:
        runtime = Runtime.create(settings)
        try:
            return await execute(runtime, args.name)
        except Exception:
            return False
        finally:
            await runtime.dispose()

    return 0 if asyncio.run(run()) else 1


def cmd_check(_: argparse.Namespace) -> int:
    from jobbot.health import check_database
    from jobbot.runtime import Runtime

    settings = _settings()

    async def run() -> int:
        runtime = Runtime.create(settings)
        try:
            check = await check_database(runtime.engine)
        finally:
            await runtime.dispose()
        print(f"configuration : ok (env={settings.env.value})")
        if not check.ok:
            print(f"base de données : injoignable ({check.error})")
            return 1
        state = "à jour" if check.up_to_date else f"à migrer (attendu {check.head})"
        print(f"base de données : ok, migration {check.revision} {state}")
        return 0 if check.up_to_date else 1

    return asyncio.run(run())


def cmd_openapi(_: argparse.Namespace) -> int:
    from jobbot.api.app import create_app

    # Aucune connexion n'est ouverte : l'URL ne sert qu'à construire l'application.
    settings = Settings(database_url="postgresql+psycopg://openapi@localhost/openapi")
    print(json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False))
    return 0


def cmd_imap_sample(args: argparse.Namespace) -> int:
    from datetime import UTC, datetime, timedelta

    from jobbot.mail.imap import ImapMailbox, MailboxError
    from jobbot.storage.base import create_storage

    settings = _settings()
    if not settings.imap_configured:
        print(
            "Collecte non configurée : JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD.", file=sys.stderr
        )
        return 1
    since = (datetime.now(UTC) - timedelta(days=settings.imap_backfill_days)).date()
    try:
        emails = ImapMailbox.from_settings(settings).fetch_since(
            since, limit=args.limit, skip_message_ids=lambda _: set(), newest_first=True
        )
    except MailboxError as exc:
        print(f"Erreur IMAP : {exc}", file=sys.stderr)
        return 1
    storage = create_storage(settings)
    for email in emails:
        storage.put(f"samples/{email.uid:08d}.eml", email.raw)
    print(f"{len(emails)} e-mail(s) copié(s) dans {settings.storage_path / 'samples'}")
    return 0


def cmd_reparse(args: argparse.Namespace) -> int:
    from jobbot.collect.service import reparse
    from jobbot.db.models import Source
    from jobbot.runtime import Runtime

    settings = _settings()

    async def run() -> int:
        runtime = Runtime.create(settings)
        try:
            source = Source(args.source) if args.source else None
            result = await reparse(runtime, source=source)
        finally:
            await runtime.dispose()
        print(
            f"{result.examined} alerte(s) examinée(s), {result.updated} mise(s) à jour, "
            f"{result.new_offers} nouvelle(s) offre(s), {result.missing_raw} copie(s) manquante(s)"
        )
        return 0

    return asyncio.run(run())


def cmd_anonymize_sample(args: argparse.Namespace) -> int:
    from pathlib import Path

    from sqlalchemy import select

    from jobbot.db.models import Search
    from jobbot.mail.anonymize import anonymize
    from jobbot.runtime import Runtime

    settings = _settings()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    async def run() -> int:
        runtime = Runtime.create(settings)
        try:
            async with runtime.sessionmaker() as session:
                rows = list(await session.scalars(select(Search).where(Search.id.in_(args.ids))))
        finally:
            await runtime.dispose()
        for index, search in enumerate(sorted(rows, key=lambda s: s.id), start=1):
            target = out / f"{search.source}-{index}.eml"
            target.write_bytes(anonymize(runtime.storage.get(search.raw_key), index=index))
            print(f"alerte {search.id} → {target}")
        print("À relire avant tout commit : le dépôt est public.")
        return 0

    return asyncio.run(run())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobbot", description="job-bot")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("api", help="API HTTP").set_defaults(func=cmd_api)
    sub.add_parser("worker", help="file de tâches").set_defaults(func=cmd_worker)
    sub.add_parser("migrate", help="applique les migrations").set_defaults(func=cmd_migrate)
    run_job = sub.add_parser("run-job", help="exécute une tâche une fois")
    run_job.add_argument("name")
    run_job.set_defaults(func=cmd_run_job)
    sub.add_parser("check", help="vérifie configuration et base").set_defaults(func=cmd_check)
    sub.add_parser("openapi", help="schéma OpenAPI sur stdout").set_defaults(func=cmd_openapi)
    sample = sub.add_parser("imap-sample", help="copie des e-mails pour écrire les analyseurs")
    sample.add_argument("--limit", type=int, default=30)
    sample.set_defaults(func=cmd_imap_sample)
    reparse = sub.add_parser("reparse", help="réanalyse les copies brutes stockées")
    reparse.add_argument("--source", choices=["jobup", "indeed", "jobroom", "unknown"])
    reparse.set_defaults(func=cmd_reparse)
    anon = sub.add_parser("anonymize-sample", help="jeux de test anonymisés")
    anon.add_argument("ids", nargs="+", type=int, help="identifiants d'alertes (journal)")
    anon.add_argument("--out", required=True, help="dossier de sortie")
    anon.set_defaults(func=cmd_anonymize_sample)
    args = parser.parse_args(argv)
    code: int = args.func(args)
    return code


if __name__ == "__main__":
    sys.exit(main())
