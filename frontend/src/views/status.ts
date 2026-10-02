import type { StatusResponse } from "../api/client";

export type Level = "ok" | "warn" | "down";

export interface Indicator {
  label: string;
  level: Level;
  detail: string;
}

const relative = new Intl.RelativeTimeFormat("fr", { numeric: "auto" });

export function sinceText(iso: string, now: Date = new Date()): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const minutes = Math.round(seconds / 60);
  if (Math.abs(seconds) < 60) return relative.format(seconds, "second");
  if (Math.abs(minutes) < 60) return relative.format(minutes, "minute");
  return relative.format(Math.round(minutes / 60), "hour");
}

/** Traduit la réponse de /api/status (ou son absence) en trois voyants. */
export function indicators(status: StatusResponse | null, now: Date = new Date()): Indicator[] {
  if (status === null) {
    return [
      { label: "API", level: "down", detail: "injoignable" },
      { label: "Base de données", level: "down", detail: "inconnue (API injoignable)" },
      { label: "Worker", level: "down", detail: "inconnu (API injoignable)" },
      { label: "Collecte", level: "down", detail: "inconnue (API injoignable)" },
    ];
  }

  const { database, worker, collect } = status;
  let db: Indicator;
  if (!database.ok) {
    db = { label: "Base de données", level: "down", detail: `injoignable (${database.error ?? "erreur"})` };
  } else if (!database.up_to_date) {
    db = {
      label: "Base de données",
      level: "warn",
      detail: `migration ${database.revision ?? "aucune"}, attendue ${database.head ?? "?"} : lancer make migrate`,
    };
  } else {
    db = { label: "Base de données", level: "ok", detail: `migration ${database.revision}` };
  }

  let wk: Indicator;
  if (worker.healthy && worker.last_heartbeat_at) {
    wk = { label: "Worker", level: "ok", detail: `dernier heartbeat ${sinceText(worker.last_heartbeat_at, now)}` };
  } else if (worker.last_heartbeat_at) {
    wk = { label: "Worker", level: "down", detail: `silencieux, dernier heartbeat ${sinceText(worker.last_heartbeat_at, now)}` };
  } else {
    wk = { label: "Worker", level: "down", detail: "aucun heartbeat reçu" };
  }

  let col: Indicator;
  if (!collect.configured) {
    col = { label: "Collecte", level: "warn", detail: "non configurée : JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD" };
  } else if (collect.last_error) {
    col = { label: "Collecte", level: "down", detail: `dernière collecte en échec : ${collect.last_error}` };
  } else if (collect.last_success_at) {
    col = { label: "Collecte", level: "ok", detail: `dernière collecte ${sinceText(collect.last_success_at, now)}` };
  } else {
    col = { label: "Collecte", level: "warn", detail: "configurée, pas encore exécutée" };
  }

  return [{ label: "API", level: "ok", detail: `version ${status.version} (${status.env})` }, db, wk, col];
}
