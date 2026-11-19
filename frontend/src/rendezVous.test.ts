import { describe, expect, it } from "vitest";

import type { Application } from "./api/client";
import type { components } from "./api/schema";
import {
  appointmentMatches,
  meetingMatches,
  searchWords,
  agreedLines,
  countdown,
  dateText,
  interviewPlace,
  interviewsToNote,
  meetingsToNote,
  notedInterviews,
  notedMeetings,
  pointDone,
  notedSummary,
  pastTitle,
  sheetLines,
  splitLine,
  upcomingAppointments,
  upcomingLabel,
  upcomingLine,
  upcomingWhen,
  upcomingWhere,
  type Upcoming,
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
  it("la date en texte et le compte à rebours", () => {
    expect(dateText("2026-11-10T08:30:00Z")).toBe("Mardi 10 novembre");
    expect(countdown("2026-11-10T08:30:00Z", NOW)).toBe("Dans 4 jours");
    expect(countdown("2026-11-07T08:30:00Z", NOW)).toBe("Demain");
    expect(countdown("2026-11-06T15:00:00Z", NOW)).toBe("Aujourd’hui");
  });

  it("la 2e ligne d’une carte « À venir » : heure · délai, puis le lieu s’il existe (§39 du 16.11)", () => {
    const [orp] = upcomingAppointments(meeting("2026-11-10T08:00:00Z"), [], NOW) as [Upcoming];
    expect(upcomingLine(orp, NOW)).toBe("9 h · dans 4 jours · ORP Renens");
    const [noPlace] = upcomingAppointments({ ...meeting("2026-11-07T08:00:00Z"), place: " " }, [], NOW) as [Upcoming];
    expect(upcomingLine(noPlace, NOW)).toBe("9 h · demain");
    const job = { ...application(1, "2026-11-09T13:00:00Z"), interview_format: "visio" } as Application;
    const [interview] = upcomingAppointments(null, [job], NOW) as [Upcoming];
    // L'heure et le délai d'abord : ils ne sont jamais coupés ; l'entreprise, le format et le lieu suivent.
    expect(upcomingWhen(interview, NOW)).toBe("14 h · dans 3 jours");
    expect(upcomingWhere(interview)).toBe("Entreprise 1 · Visio");
    expect(upcomingLine(interview, NOW)).toBe("14 h · dans 3 jours · Entreprise 1 · Visio");
  });

  it("le nom de la carte : titre, pastille, date et heure, délai, lieu (§39 du 16.11)", () => {
    const [orp] = upcomingAppointments(meeting("2026-11-10T08:00:00Z"), [], NOW) as [Upcoming];
    expect(upcomingLabel(orp, "Feuille prête", NOW)).toBe("Rendez-vous ORP, feuille prête, mardi 10 novembre à 9 h, dans 4 jours, ORP Renens");
    const [interview] = upcomingAppointments(null, [application(1, "2026-11-09T13:00:00Z")], NOW) as [Upcoming];
    expect(upcomingLabel(interview, "À préparer", NOW)).toBe("Poste 1, Entreprise 1, à préparer, lundi 9 novembre à 14 h, dans 3 jours");
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

describe("recherche de l'onglet Rendez-vous (maquette du 14 novembre, §6)", () => {
  const meeting = { place: "ORP de Lausanne" } as never;
  const interview = {
    kind: "entretien",
    key: "entretien-1",
    at: "2026-11-19T09:00:00Z",
    application: { job_title: "Site Reliability Engineer", company: "Essai Systèmes SA", location: "Renens", interview_place: null, company_address: "Rue de l'Exemple 3", interview_format: null },
  } as never;

  it("découpe sans accents ni casse", () => {
    expect(searchWords("  Systèmes  RENENS ")).toEqual(["systemes", "renens"]);
  });

  it("un rendez-vous ORP par « ORP » ou son lieu, un entretien par poste, entreprise ou lieu", () => {
    expect(meetingMatches(meeting, searchWords("orp lausanne"))).toBe(true);
    expect(meetingMatches(meeting, searchWords("genève"))).toBe(false);
    expect(appointmentMatches(interview, searchWords("essai reliability"))).toBe(true);
    expect(appointmentMatches(interview, searchWords("exemple"))).toBe(true);
    expect(appointmentMatches(interview, searchWords("orp"))).toBe(false);
    expect(appointmentMatches(interview, [])).toBe(true);
  });
});

describe("Faire le point sur ordinateur (planche FairePointOrdinateur, accord de Kevin du 19.11)", () => {
  const withInterviews = (id: number, interview_at: string, interviews: object[], status = "entretien") =>
    ({ ...application(id, interview_at, status), interviews }) as unknown as Application;

  it("« À noter » : l'entretien passé sans retour ce jour-là, du plus récent au plus ancien", () => {
    const items = interviewsToNote(
      [
        withInterviews(1, "2026-11-02T13:00:00Z", []),
        withInterviews(2, "2026-11-05T13:00:00Z", []),
        withInterviews(3, "2026-11-04T13:00:00Z", [{ id: 9, held_at: "2026-11-04" }]),
        withInterviews(4, "2026-11-10T13:00:00Z", []),
        withInterviews(5, "2026-11-03T13:00:00Z", [], "refus"),
        // Comme le badge de l'onglet : pas le jour même, et 14 jours au plus.
        withInterviews(6, "2026-11-06T07:00:00Z", []),
        withInterviews(7, "2026-10-22T13:00:00Z", []),
        withInterviews(8, "2026-10-23T13:00:00Z", []),
      ],
      NOW,
    );
    expect(items.map((i) => i.key)).toEqual(["point-2", "point-1", "point-8"]);
  });

  it("« Passés » : chaque retour fait, avec l'heure seulement pour l'entretien prévu", () => {
    const items = notedInterviews(
      [
        withInterviews(1, "2026-11-04T13:00:00Z", [
          { id: 7, held_at: "2026-10-20", feeling: null },
          { id: 8, held_at: "2026-11-04", feeling: "moyen" },
        ]),
      ],
      NOW,
    );
    expect(items.map((i) => [i.key, i.at])).toEqual([
      ["retour-8", "2026-11-04T13:00:00Z"],
      ["retour-7", "2026-10-20T00:00:00"],
    ]);
    expect(pointDone(items[0]!.interview)).toBe("Point fait · Moyen");
    expect(pointDone(items[1]!.interview)).toBe("Point fait");
  });
});
