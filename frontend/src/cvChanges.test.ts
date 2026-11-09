import { describe, expect, it } from "vitest";

import type { Cv } from "./api/client";
import { cvChanges } from "./cvChanges";

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

  it("un nouvel ordre dans une rubrique : annuler remet l'ordre d'origine aux mêmes places", () => {
    const [change] = cvChanges(cv([3, 1, 2, 4]));
    expect(change).toMatchObject({ title: "Expériences", before: "Avant : « Projet perso » venait en 3e position." });
    expect(change!.now).toBe("Maintenant : il vient en première position, pour cette offre.");
    expect(change!.undo).toEqual([1, 2, 3, 4]);
  });

  it("un bloc retiré : annuler le remet entre ses voisins d'origine", () => {
    const changes = cvChanges(cv([1, 3, 4]));
    expect(changes).toHaveLength(1);
    expect(changes[0]).toMatchObject({ title: "Stage web", now: "Maintenant : retiré pour cette offre.", undo: [1, 2, 3, 4] });
  });

  it("le résumé est un point à vérifier, sans annulation", () => {
    const [change] = cvChanges(cv([1, 2, 3, 4], "Ingénieur DevOps."));
    expect(change).toMatchObject({ title: "Profil", now: "Maintenant : « Ingénieur DevOps. »", undo: null });
  });

  it("sans ordre d'origine (ancienne réponse), seul le résumé compte", () => {
    const old = { ...cv([2, 1], "Résumé."), origin_ids: undefined } as unknown as Cv;
    expect(cvChanges(old).map((c) => c.key)).toEqual(["summary"]);
  });
});
