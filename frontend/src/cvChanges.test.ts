import { describe, expect, it } from "vitest";

import type { Cv } from "./api/client";
import { canUndo, cvChanges, employerOf } from "./cvChanges";

const BLOCKS = [
  { id: 1, title: "Stage DevOps", section: "experience" },
  { id: 2, title: "Stage web", section: "experience" },
  { id: 3, title: "Projet perso", section: "experience" },
  { id: 4, title: "Kubernetes", section: "competence" },
];

function cv(chunkIds: number[], summary = ""): Cv {
  return {
    summary,
    chunk_ids: chunkIds,
    origin_ids: [1, 2, 3, 4],
    blocks: BLOCKS.map((b) => ({ ...b, selected: chunkIds.includes(b.id) })),
  } as unknown as Cv;
}

describe("cvChanges", () => {
  it("rien de changé : aucun point", () => {
    expect(cvChanges(cv([1, 2, 3, 4]))).toEqual([]);
  });

  it("un nouvel ordre dans une rubrique : annuler remet l’ordre d’origine aux mêmes places", () => {
    const [change] = cvChanges(cv([3, 1, 2, 4]));
    expect(change).toMatchObject({ title: "Expériences", before: "Avant : « Projet perso » venait en 3e position." });
    expect(change!.now).toBe("Maintenant : il vient en premier.");
    expect(change!.undo).toEqual([1, 2, 3, 4]);
  });

  it("un bloc retiré : annuler le remet entre ses voisins d’origine", () => {
    const changes = cvChanges(cv([1, 3, 4]));
    expect(changes).toHaveLength(1);
    expect(changes[0]).toMatchObject({ title: "Stage web", now: "Maintenant : retiré pour cette offre.", undo: [1, 2, 3, 4] });
  });

  it("le résumé s’annule : sans résumé de départ, « Annuler » le retire (Kevin, 19.11)", () => {
    const [change] = cvChanges(cv([1, 2, 3, 4], "Ingénieur DevOps."));
    expect(change).toMatchObject({ title: "Profil", now: "Maintenant : « Ingénieur DevOps. »", summaryUndo: "" });
    expect(change!.before).toBe("Avant : pas de résumé ; jobA1 l’écrit à partir de tes blocs, sans rien ajouter.");
    expect(canUndo(change!)).toBe(true);
  });

  it("le résumé de la version de départ : « Avant » le cite, « Annuler » le remet ; inchangé, aucun point", () => {
    const next = { ...cv([1, 2, 3, 4], "Ingénieur DevOps et Kubernetes."), origin_summary: "Ingénieur DevOps." } as Cv;
    const [change] = cvChanges(next);
    expect(change).toMatchObject({ before: "Avant : « Ingénieur DevOps. »", summaryUndo: "Ingénieur DevOps." });
    expect(cvChanges({ ...next, summary: "Ingénieur DevOps." })).toEqual([]);
  });

  it("une expérience déplacée : « Expérience chez <entreprise> », sinon « Expériences »", () => {
    expect(employerOf("Stage développeur web / administrateur système — Retraites Populaires (01 – 07.2024)")).toEqual({
      role: "Stage développeur web / administrateur système",
      company: "Retraites Populaires",
    });
    expect(employerOf("Ingénieur·e DevOps, Exemple Logistique SA (2021-2026)")?.company).toBe("Exemple Logistique SA");
    expect(employerOf("DevOps Engineer · Nordwind Cloud")?.company).toBe("Nordwind Cloud");
    expect(employerOf("Projet perso")).toBeNull();
    const named = { ...cv([2, 1, 3, 4]) } as Cv;
    named.blocks = named.blocks.map((b) => (b.id === 2 ? { ...b, title: "Développeur, Nordwind Cloud (2024)" } : b));
    expect(cvChanges(named)[0]).toMatchObject({
      title: "Expérience chez Nordwind Cloud",
      before: "Avant : « Développeur » venait en 2e position.",
    });
  });

  it("sans ordre d’origine (ancienne réponse), seul le résumé compte", () => {
    const old = { ...cv([2, 1], "Résumé."), origin_ids: undefined } as unknown as Cv;
    expect(cvChanges(old).map((c) => c.key)).toEqual(["summary"]);
  });
});
