import { describe, expect, it } from "vitest";

import type { Application } from "./api/client";
import type { components } from "./api/schema";
import {
  agreedLines,
  countdown,
  dateBlock,
  dateText,
  interviewPlace,
  meetingsToNote,
  notedMeetings,
  notedSummary,
  pastTitle,
  sheetLines,
  splitLine,
  upcomingAppointments,
} from "./rendezVous";

type Meeting = components["schemas"]["MeetingOut"];

// Candidatures › Rendez-vous sur téléphone (maquette RendezVous, 6.11.2026).
const NOW = new Date("2026-11-06T09:00:00Z");
const EMPTY = { outcome_at: null, agreed_target: null, measures: [], assignments: null, note: null, asked: [], next_starts_at: null, sheet_text: null };
const meeting = (starts_at: string): Meeting => ({ id: 1, starts_at, place: "ORP Renens", advisor: null, ...EMPTY });
const application = (id: number, interview_at: string | null, status = "entretien") =>
  ({ id, company: `Entreprise ${id}`, job_title: `Poste ${id}`, status, interview_at, company_address: null }) as unknown as Application;

describe("la liste « À venir » (ORP et entretiens d’embauche)", () => {
  it("triée par date, du plus proche au plus lointain", () => {
    const items = upcomingAppointments(null, [application(1, "2026-11-16T09:00:00Z"), application(2, "2026-11-12T13:00:00Z"), application(3, "2026-11-20T08:00:00Z")], NOW);
    expect(items.map((i) => i.key)).toEqual(["entretien-2", "entretien-1", "entretien-3"]);
  });

  it("le rendez-vous ORP mêlé aux entretiens, à sa date", () => {
    const items = upcomingAppointments(
      meeting("2026-11-10T08:30:00Z"),
      [application(1, "2026-11-16T09:00:00Z"), application(2, "2026-11-08T13:00:00Z")],
      NOW,
    );
    expect(items.map((i) => i.kind)).toEqual(["entretien", "orp", "entretien"]);
    expect(items.map((i) => i.at)).toEqual(["2026-11-08T13:00:00Z", "2026-11-10T08:30:00Z", "2026-11-16T09:00:00Z"]);
  });

  it("sans rendez-vous : une liste vide (passés, sans date et refusés ne comptent pas)", () => {
    expect(upcomingAppointments(null, [], NOW)).toEqual([]);
    const items = upcomingAppointments(
      meeting("2026-11-02T08:30:00Z"),
      [application(1, null, "en_attente"), application(2, "2026-10-30T09:00:00Z"), application(3, "2026-11-12T09:00:00Z", "refus")],
      NOW,
    );
    expect(items).toEqual([]);
  });
});

describe("les textes de la carte", () => {
  it("le bloc date, la date en texte et le compte à rebours", () => {
    expect(dateBlock("2026-11-10T08:30:00Z")).toEqual({ weekday: "mar.", day: "10", month: "nov." });
    expect(dateText("2026-11-10T08:30:00Z")).toBe("Mardi 10 novembre");
    expect(countdown("2026-11-10T08:30:00Z", NOW)).toBe("Dans 4 jours");
    expect(countdown("2026-11-07T08:30:00Z", NOW)).toBe("Demain");
    expect(countdown("2026-11-06T15:00:00Z", NOW)).toBe("Aujourd’hui");
  });

  it("les trois lignes tirées de la feuille ; une partie vide ne s’affiche pas", () => {
    const prep = {
      summaries: [],
      works: null,
      blockers: ["Formulaires en ligne : 0 réponse sur 9."],
      missing: [{ skill: "Terraform", count: 14, training_id: null, training_title: null }],
      offers: 22,
      questions: [],
      obligations: [],
      has_applications: true,
      months: [{ month: "2026-11", count: 6, target: 10, answered: 0, interviews: 0 }],
    };
    expect(sheetLines(prep)).toEqual([
      { label: "Ton mois", text: "6 recherches sur 10" },
      { label: "Ce qui bloque", text: "Formulaires en ligne : 0 réponse sur 9" },
      { label: "Ce qui te manque", text: "Terraform, demandé dans 14 offres sur 22" },
    ]);
    expect(sheetLines({ ...prep, blockers: [], missing: [], months: [] })).toEqual([]);
  });

  it("le lieu de l’entretien : le lieu ou lien saisi, sinon l’adresse de l’entreprise", () => {
    expect(interviewPlace({ interview_place: "Visio", company_address: "Rue du Port 1, Lausanne" })).toBe("Visio");
    expect(interviewPlace({ interview_place: "  ", company_address: "Rue du Port 1, Lausanne" })).toBe("Rue du Port 1, Lausanne");
    expect(interviewPlace({ interview_place: null, company_address: null })).toBeNull();
  });

  it("ce qui a été convenu : objectif, mesure, prochain", () => {
    const past = {
      ...meeting("2026-10-13T08:00:00Z"),
      outcome_at: "2026-10-13T10:00:00Z",
      agreed_target: 10,
      measures: [{ text: "Cours Terraform, financement accepté", training_id: null }],
      next_starts_at: "2026-11-10T08:30:00Z",
    };
    expect(pastTitle(past.starts_at, NOW)).toBe("Rendez-vous ORP du 13 octobre");
    expect(agreedLines(past)).toEqual([
      { label: "Objectif", text: "10 recherches par mois" },
      { label: "Mesure", text: "Cours Terraform, financement accepté" },
      { label: "Prochain", text: "Mardi 10 novembre, 9 h 30" },
    ]);
  });
});

describe("« À noter » et « Derniers rendez-vous ORP » (maquettes du 7.11.2026)", () => {
  const page = (current: Meeting | null, past: Meeting[]) =>
    ({ meeting: current, past, preparation: null, target: 10, trainings: [] }) as never;

  it("un rendez-vous passé sans rien de noté est « à noter » ; noté, il passe dans les derniers", () => {
    const held = meeting("2026-10-13T08:00:00Z");
    const noted = { ...meeting("2026-09-15T08:00:00Z"), id: 2, outcome_at: "2026-09-15T10:00:00Z", agreed_target: 8 };
    expect(meetingsToNote(page(held, [noted]), NOW).map((m) => m.id)).toEqual([1]);
    expect(notedMeetings(page(held, [noted]), NOW).map((m) => m.id)).toEqual([2]);
  });

  it("un rendez-vous à venir n’est pas à noter", () => {
    expect(meetingsToNote(page(meeting("2026-11-10T08:30:00Z"), []), NOW)).toEqual([]);
  });

  it("le résumé d’un rendez-vous noté", () => {
    const noted = { ...meeting("2026-09-15T08:00:00Z"), agreed_target: 8, measures: [{ text: "Financement Terraform", training_id: null }] };
    expect(notedSummary(noted)).toBe("Objectif 8 par mois · financement Terraform");
    expect(notedSummary(meeting("2026-09-15T08:00:00Z"))).toBe("Rien de particulier");
  });

  it("une ligne de la feuille en titre et précision", () => {
    expect(splitLine("Formulaires en ligne : 0 réponse sur 9.")).toEqual({ main: "Formulaires en ligne", sub: "0 réponse sur 9." });
    expect(splitLine("Terraform")).toEqual({ main: "Terraform", sub: "" });
  });
});
