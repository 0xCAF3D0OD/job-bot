// Le détail d'une candidature envoyée (§8 du 9 novembre) : mots de statut, Suivi en 5 étapes, Historique.
import { describe, expect, it } from "vitest";

import { sentHistory, sentSteps, sentWords } from "./sentDetail";

const now = new Date("2026-11-08T10:00:00");
const base = {
  id: 1,
  sent_at: "2026-09-13",
  method: "electronique",
  company: "Lombard Odier & Cie",
  job_title: "Internship",
  status: "en_attente",
  application_url: "https://www.linkedin.com/jobs/1",
  letter_draft_id: 4,
  cv_draft_id: 5,
  orp_month: "2026-09",
  follow_up_on: null,
  followed_up_at: null,
  interviews: [],
  contacts: [],
} as never;
const declared = { declared_at: "2026-10-05", missing: [] } as never;

describe("Les mots de statut", () => {
  it("« Sans réponse · 56 jours » en pêche, puis « Déclarée à l’ORP » coché en vert", () => {
    const words = sentWords(base, declared, now);
    expect(words.map((w) => [w.text, w.tone])).toEqual([
      ["Sans réponse · 56 jours", "peach"],
      ["Déclarée à l’ORP", "green"],
    ]);
    expect(words[1]!.check).toBe(true);
  });

  it("refus en gris, sans « Déclarée » quand rien n’est déclaré", () => {
    expect(sentWords({ ...(base as object), status: "refus" } as never, null, now).map((w) => w.text)).toEqual(["Refus"]);
  });
});

describe("Le Suivi en 5 étapes", () => {
  it("relance conseillée : les trois premières faites, la relance en cours, la réponse en attente", () => {
    const steps = sentSteps(base, declared, now);
    expect(steps.map((s) => s.label)).toEqual(["Préparée", "Envoyée", "Déclarée ORP", "Relance", "Réponse"]);
    expect(steps.map((s) => s.state)).toEqual(["done", "done", "done", "current", "todo"]);
    expect(steps.map((s) => s.sub)).toEqual(["Lettre et CV", "13 sept.", "5 oct.", "conseillée", "en attente"]);
  });

  it("pas encore déclarée : l’étape ORP est en cours et « à faire »", () => {
    const steps = sentSteps(base, { declared_at: null, missing: [] } as never, now);
    expect(steps[2]).toEqual({ label: "Déclarée ORP", sub: "à faire", state: "current" });
    expect(steps[3]!.state).toBe("todo");
  });

  it("une réponse reçue : tout est fait, la relance n’était pas utile", () => {
    const steps = sentSteps({ ...(base as object), status: "entretien" } as never, declared, now);
    expect(steps.every((s) => s.state === "done")).toBe(true);
    expect(steps[3]!.sub).toBe("pas besoin");
    expect(steps[4]!.sub).toBe("Entretien");
  });
});

describe("L’Historique", () => {
  it("du plus récent au plus ancien : déclaration (formulaire du mois), puis l’envoi avec le site et les documents", () => {
    expect(sentHistory(base, declared, now)).toEqual([
      { day: "2026-10-05", date: "5 oct.", title: "Déclarée à l’ORP", detail: "Formulaire de septembre" },
      { day: "2026-09-13", date: "13 sept.", title: "Candidature envoyée sur linkedin.com", detail: "Lettre et CV adapté" },
    ]);
  });

  it("une prise de contact et une relance s’y ajoutent", () => {
    const a = {
      ...(base as object),
      status: "relancee",
      followed_up_at: "2026-10-20",
      contacts: [{ name: null, role: "recruiter", channel: "linkedin_message", contacted_on: "2026-10-25", answered_on: null }],
    } as never;
    expect(sentHistory(a, null, now).map((e) => e.title)).toEqual([
      "Contact : Recrutement",
      "Relance envoyée",
      "Candidature envoyée sur linkedin.com",
    ]);
  });
});
