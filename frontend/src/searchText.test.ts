import { describe, expect, it } from "vitest";

import { andList, applicationLine, companyLine, followMessage } from "./searchText";

const follow = (todo: string[], sites = ["jobup", "jobs.ch", "LinkedIn", "Indeed"]) => ({
  ids: [1],
  created: [1],
  terms: "kubernetes",
  locations: ["Zurich"],
  sites,
  todo,
});

describe("textes de la recherche globale", () => {
  it("une liste en mots", () => {
    expect([andList([]), andList(["jobup"]), andList(["jobup", "Indeed"]), andList(["a", "b", "c"])]).toEqual([
      "",
      "jobup",
      "jobup et Indeed",
      "a, b et c",
    ]);
  });

  it("tous les sites à créer : « ajoutée », jamais « suivie », la phrase orange", () => {
    expect(followMessage(follow(["jobup", "jobs.ch", "LinkedIn", "Indeed"]))).toEqual({
      title: "Recherche ajoutée : kubernetes · Zurich · jobup, jobs.ch, LinkedIn, Indeed",
      todo: "Il te reste à créer l'alerte sur chaque site : jobup, jobs.ch, LinkedIn et Indeed. Tant qu'elle n'est pas créée, rien n'arrive.",
    });
  });

  it("une partie des sites à créer : seulement ceux-là", () => {
    expect(followMessage(follow(["LinkedIn"])).todo).toBe(
      "Il te reste à créer l'alerte sur LinkedIn. Tant qu'elle n'est pas créée, rien n'arrive.",
    );
    expect(followMessage(follow(["LinkedIn"])).title).toMatch(/^Recherche ajoutée/);
  });

  it("aucun site à créer : « suivie », sans phrase orange", () => {
    expect(followMessage(follow([]))).toEqual({
      title: "Recherche suivie : kubernetes · Zurich · jobup, jobs.ch, LinkedIn, Indeed",
      todo: null,
    });
  });

  it("la phrase d'une candidature et d'une entreprise", () => {
    const now = new Date("2026-10-22T10:00:00Z");
    const hit = { id: 1, company: "Démo Data SA", job_title: "x", status: "en_attente", sent_at: "2026-10-12", interview_at: null, orp_month: "2026-10" };
    expect(applicationLine(hit, now)).toBe("Démo Data SA · envoyée le 12 oct.");
    expect(applicationLine({ ...hit, interview_at: "2026-10-29T08:00:00Z" }, now)).toBe("Démo Data SA · entretien le 29 oct.");
    expect(companyLine({ name: "x", offers: 2, applications: 1 })).toBe("2 offres, 1 candidature");
    expect(companyLine({ name: "x", offers: 0, applications: 3 })).toBe("3 candidatures");
  });
});
