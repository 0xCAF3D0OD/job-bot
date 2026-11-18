// Le détail d'une candidature envoyée (§8 du 9 novembre) : mots de statut, Suivi en 5 étapes, Historique.
import { describe, expect, it } from "vitest";

import { orpTodo, phoneSteps, sentHistory, sentSteps, sentWords } from "./sentDetail";
import { sentWhen } from "./sentList";

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

describe("Téléphone : la frise de 4 étapes (EnvoyeeDetail, §40)", () => {
  const states = (extra: object) => phoneSteps({ ...(base as object), ...extra } as never).map((s) => `${s.label}:${s.state}`);
  it("en attente : Réponse en cours", () => {
    expect(states({})).toEqual(["Envoyée:done", "Réponse:current", "Entretien:todo", "Décision:todo"]);
  });
  it("entretien à venir : Entretien en cours ; passé : Décision en cours", () => {
    expect(states({ status: "entretien" })).toEqual(["Envoyée:done", "Réponse:done", "Entretien:current", "Décision:todo"]);
    expect(states({ status: "entretien", interviews: [{ held_at: "2026-11-02", rating: 4 }] })).toEqual(["Envoyée:done", "Réponse:done", "Entretien:done", "Décision:current"]);
  });
  it("refus sans entretien : l’étape Entretien reste grise, la décision est faite", () => {
    expect(states({ status: "refus" })).toEqual(["Envoyée:done", "Réponse:done", "Entretien:todo", "Décision:done"]);
  });
});

describe("Téléphone : la ligne « entreprise · quand » d’une carte d’Envoyées (§27)", () => {
  const a = (extra: object) => ({ ...(base as object), ...extra }) as never;
  it("à relancer : il y a N j, depuis la relance s’il y en a une", () => {
    expect(sentWhen(a({ sent_at: "2026-10-27" }), "follow", now)).toBe("il y a 12 j");
    expect(sentWhen(a({ status: "relancee", followed_up_at: "2026-11-01" }), "follow", now)).toBe("il y a 7 j");
  });
  it("entretien : le jour court et l’heure ; réponse reçue ; sinon le jour d’envoi", () => {
    expect(sentWhen(a({ status: "entretien", interview_at: "2026-11-12T13:00:00Z" }), "interviews", now)).toBe("jeu. 12 nov., 14 h");
    expect(sentWhen(a({ status: "refus", status_at: "2026-11-07T09:00:00Z" }), "earlier", now)).toBe("réponse hier");
    expect(sentWhen(a({ sent_at: "2026-11-03" }), "week", now)).toBe("mardi");
    expect(sentWhen(a({ sent_at: "2026-10-21" }), "earlier", now)).toBe("21 oct.");
  });
});

describe("orpTodo : ce qui reste à faire pour l’ORP (Kevin, 18.11)", () => {
  it("rien sans ligne ORP ni quand tout est déclaré ; sinon déclarer, puis compléter", () => {
    expect(orpTodo(null)).toBeNull();
    expect(orpTodo({ declared_at: "2026-10-05", missing: [] } as never)).toBeNull();
    expect(orpTodo({ declared_at: null, missing: ["Adresse"] } as never)).toEqual({ text: "À déclarer à l’ORP", tone: "blue", test: "word-to-declare" });
    expect(orpTodo({ declared_at: "2026-10-05", missing: ["Adresse"] } as never)).toEqual({ text: "À compléter pour l’ORP", tone: "orange", test: "word-to-complete" });
  });
  it("« Déclarée à l’ORP » seulement si la déclaration est complète", () => {
    const words = (missing: string[]) => sentWords(base, { declared_at: "2026-10-05", missing } as never, now).map((w) => w.test);
    expect(words([])).toContain("word-declared");
    expect(words(["Adresse"])).not.toContain("word-declared");
  });
});
