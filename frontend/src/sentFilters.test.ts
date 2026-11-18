import { describe, expect, it } from "vitest";

import type { Application } from "./api/client";
import { sentCounts, sentFilterOf, sentFiltered } from "./sentFilters";

const app = (id: number, status: Application["status"]) => ({ id, status, sent_at: "2026-11-17" }) as Application;
const all = [app(1, "en_attente"), app(2, "relancee"), app(3, "sans_reponse"), app(4, "reponse"), app(5, "entretien"), app(6, "refus"), app(7, "engagement")];

describe("les statuts des Envoyées (Kevin, 18.11)", () => {
  it("« Envoyée » regroupe les candidatures sans réponse de l’employeur", () => {
    expect(sentFiltered(all, "envoyee").map((a) => a.id)).toEqual([1, 2, 3]);
  });
  it("« Réponse reçue », « Entretien » et « Refusée » suivent chacun leur statut", () => {
    expect(sentFiltered(all, "reponse").map((a) => a.id)).toEqual([4]);
    expect(sentFiltered(all, "entretien").map((a) => a.id)).toEqual([5]);
    expect(sentFiltered(all, "refusees").map((a) => a.id)).toEqual([6]);
    expect(sentCounts(all).toutes).toBe(7);
  });
  it("une ancienne adresse ?statut=sans-reponse ouvre « Envoyée »", () => {
    expect(sentFilterOf("sans-reponse")).toBe("envoyee");
    expect(sentFilterOf("vue")).toBe("toutes");
  });
});
