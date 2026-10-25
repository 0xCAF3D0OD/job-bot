import type { AlertsPage } from "./api/client";

// L'état des recherches suivies (docs/21 §4), pour le résumé et la phrase de conclusion de la
// page Alertes (1.6.22).

// Rien reçu 24 heures après la création : l'aide (docs/121 §B.3).
const WAIT_HOURS = 24;

type Cell = AlertsPage["searches"][number]["cells"][number];
const late = (cell: Cell): boolean =>
  cell.status === "created" && !!cell.created_at && Date.now() - Date.parse(cell.created_at) > WAIT_HOURS * 3_600_000;

export function alertRows(page: AlertsPage) {
  return page.searches
    .filter((s) => s.active)
    .map((search) => {
      const received = search.cells.filter((c) => c.status === "received");
      const waiting = search.cells.filter(late);
      const lastReceived = received.map((c) => c.received_at!).sort().at(-1) ?? null;
      const state = received.length ? "ok" : waiting.length ? "late" : search.cells.some((c) => c.created_at) ? "pending" : "todo";
      return { search, received, waiting, lastReceived, state };
    });
}

// Le nombre de recherches suivies (créées ou déjà reçues) et la dernière alerte reçue.
export function alertsDigest(page: AlertsPage): { active: number; lastReceived: string | null } {
  const rows = alertRows(page);
  return {
    active: rows.filter((r) => r.received.length || r.search.cells.some((c) => c.created_at)).length,
    lastReceived: rows.map((r) => r.lastReceived).filter(Boolean).sort().at(-1) ?? null,
  };
}
