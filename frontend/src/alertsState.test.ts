import { describe, expect, it } from "vitest";

import type { AlertsPage } from "./api/client";
import { NOTHING_YET_DAYS, QUIET_DAYS, alertsBand, placeLabel, searchGroups, siteState } from "./alertsState";
import { onDay } from "./format";

const NOW = new Date("2026-10-27T12:00:00Z");
const ago = (days: number) => new Date(NOW.getTime() - days * 86_400_000).toISOString();

function page(extra: Partial<AlertsPage> = {}): AlertsPage {
  const cell = (site: string, status: string, received: number | null, created: number | null) => ({
    site,
    url: `https://${site}.ch`,
    status,
    received_at: received === null ? null : ago(received),
    created_at: created === null ? null : ago(created),
    remote_url: null,
  });
  return {
    mailbox: null,
    folder: null,
    personal_address: null,
    guest_mailbox: false,
    sites: [
      { slug: "jobup", name: "jobup", senders: [], prefilled: true },
      { slug: "linkedin", name: "LinkedIn", senders: [], prefilled: true },
      { slug: "jobsch", name: "jobs.ch", senders: [], prefilled: true },
    ],
    searches: [
      { id: 1, terms: "Linux", location: "lausanne", active: true, cells: [cell("jobup", "received", 5, 20), cell("linkedin", "created", null, 5), cell("jobsch", "todo", null, null)] },
      { id: 2, terms: "Linux", location: "geneve", active: true, cells: [cell("jobup", "received", 2, 20), cell("linkedin", "todo", null, null), cell("jobsch", "todo", null, null)] },
    ],
    to_confirm: [],
    codes: [],
    ...extra,
  } as AlertsPage;
}

describe("état des alertes (planche « 6. Alertes »)", () => {
  it("les deux délais nommés", () => {
    expect([NOTHING_YET_DAYS, QUIET_DAYS]).toEqual([3, 14]);
  });

  it("jamais rien reçu : en attente à 2 jours, orange à 3", () => {
    expect(siteState({ status: "created", received_at: null, created_at: ago(2) }, NOW).kind).toBe("waiting");
    expect(siteState({ status: "created", received_at: null, created_at: ago(2) }, NOW).label).toBe("En attente du premier envoi");
    const silent = siteState({ status: "created", received_at: null, created_at: ago(3) }, NOW);
    expect(silent).toEqual({ kind: "silent", label: "Rien reçu depuis la création", days: 3 });
  });

  it("déjà reçu : la date à 13 jours, la mention grise à 14", () => {
    expect(siteState({ status: "received", received_at: ago(13), created_at: null }, NOW).kind).toBe("received");
    expect(siteState({ status: "received", received_at: "2026-10-22T07:12:00Z", created_at: null }, NOW).label).toBe("Reçue le 22 oct.");
    expect(siteState({ status: "received", received_at: ago(14), created_at: null }, NOW)).toEqual({
      kind: "quiet",
      label: "rien depuis 14 jours",
      days: 14,
    });
    expect(siteState({ status: "todo", received_at: null, created_at: null }, NOW).kind).toBe("todo");
  });

  it("les lieux avec majuscule et accents", () => {
    expect(["geneve", "VD", "valais", "Lausanne", "neuchâtel", "la sarraz"].map(placeLabel)).toEqual([
      "Genève",
      "Vaud",
      "Valais",
      "Lausanne",
      "Neuchâtel",
      "La Sarraz",
    ]);
  });

  it("une carte par recherche, ses lieux réunis, la meilleure cellule par site", () => {
    const [linux] = searchGroups(page(), NOW);
    expect(linux!.locations).toEqual(["Lausanne", "Genève"]);
    expect(linux!.ids).toEqual([1, 2]);
    expect(linux!.sites.map((s) => [s.name, s.state.kind])).toEqual([
      ["jobup", "received"],
      ["LinkedIn", "silent"],
      ["jobs.ch", "todo"],
    ]);
    // jobup : la réception la plus récente des deux lieux.
    expect(linux!.sites[0]!.state.label).toBe(`Reçue ${onDay(ago(2), NOW)}`);
    expect(linux!.pill).toEqual({ kind: "received", label: "Reçue · jobup" });
  });

  it("la bande : un code d'abord, puis une confirmation, puis l'alerte muette ; sinon rien", () => {
    const code = alertsBand(page({ codes: [{ search_id: 1, site: "jobup", code: "123456", received_at: ago(0) }] }), NOW);
    expect(code).toMatchObject({ title: "jobup attend un code de vérification.", action: "Vérifier" });
    const confirm = alertsBand(page({ to_confirm: [{ search_id: 1, site: "linkedin", subject: null, received_at: ago(0), url: "https://x" }] }), NOW);
    expect(confirm).toMatchObject({ kind: "confirm", title: "LinkedIn attend ta confirmation." });
    const silent = alertsBand(page(), NOW);
    expect(silent).toMatchObject({
      kind: "silent",
      title: "LinkedIn n'a encore rien reçu.",
      summary: "Ta recherche « Linux » y existe depuis 5 jours, sans un seul e-mail : le réglage est sans doute à revoir.",
      action: "Vérifier l'alerte",
    });
    // Une alerte créée il y a 2 jours seulement : pas de bande.
    const fresh = page();
    fresh.searches[0]!.cells[1]!.created_at = ago(2);
    expect(alertsBand(fresh, NOW)).toBeNull();
  });
});
