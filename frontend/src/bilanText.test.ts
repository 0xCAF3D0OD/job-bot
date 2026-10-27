import { describe, expect, it } from "vitest";

import { bestSite, conclusion, interviewsLine, monthLine, weakStep } from "./bilanText";

const group = (key: string, responses: number, total: number) => ({ key, label: key, responses, total, enough: total >= 5 });

describe("textes du Bilan (1.6.62)", () => {
  it("la bande : pas de site seul, ni spontanées, ni écart nul", () => {
    expect(bestSite([{ key: "source", title: "", groups: [group("jobs.ch", 3, 5)] }])).toBeNull();
    expect(bestSite([{ key: "source", title: "", groups: [group("jobs.ch", 3, 5), group("spontaneous", 0, 9)] }])).toBeNull();
    expect(bestSite([{ key: "source", title: "", groups: [group("a", 1, 5), group("b", 0, 9)] }])).toBeNull();
    expect(bestSite([{ key: "source", title: "", groups: [group("a", 4, 5), group("b", 2, 9), group("c", 1, 6)] }])?.summary).toBe(
      "Les autres sites : 3 fois sur 15.",
    );
  });

  it("l'étape faible, des offres gardées aux entretiens", () => {
    const funnel = { received: 36, retained: 33, applications: 26, responses: 10, interviews: 3, engagements: 0 };
    expect(weakStep(funnel)?.between).toBe("entre les réponses et les entretiens");
    expect(weakStep({ ...funnel, applications: 5 })?.between).toBe("entre les offres gardées et les candidatures");
    expect(weakStep({ received: 0, retained: 0, applications: 0, responses: 0, interviews: 0, engagements: 0 })).toBeNull();
  });

  it("« Par mois » et « Entretiens » repliés", () => {
    const months = [{ month: "2026-10", count: 7 }];
    expect(monthLine(months, 10, new Date(2026, 9, 27))).toBe("Octobre : 7 candidatures sur 10, il reste 4 jours");
    expect(monthLine(months, 10, new Date(2026, 9, 31))).toBe("Octobre : 7 candidatures sur 10, dernier jour");
    expect(monthLine([{ month: "2026-10", count: 1 }], null, new Date(2026, 9, 2))).toBe("Octobre : 1 candidature");
    expect(interviewsLine([])).toBe("Pas encore d'entretien");
    expect(interviewsLine([{ application_id: 1, company: "A", day: "2026-10-14", kind: null, state: "rated", rating: 3 }])).toBe(
      "1 entretien, aucun à venir",
    );
  });

  it("la conclusion : exacte dans chaque cas, testée dans l'ordre", () => {
    const at = (applications: number, responses: number, previous: number | null) =>
      conclusion(
        {
          funnel: { received: 0, retained: 0, applications, responses, interviews: 0, engagements: 0 },
          previous_responses: previous,
        } as Parameters<typeof conclusion>[0],
        "recent",
      );
    const text = (c: ReturnType<typeof conclusion>) => `${c.before}${c.accent}${c.after}`;
    expect(text(at(4, 2, 1))).toBe("Trop tôt pour conclure : 4 candidatures sur la période.");
    expect(text(at(1, 0, null))).toBe("Trop tôt pour conclure : 1 candidature sur la période.");
    // Le compte de Kevin : 19 candidatures, aucune réponse, pas de période d'avant.
    expect(at(19, 0, null)).toEqual({ before: "", accent: "Pas encore de réponse", after: " : 19 candidatures envoyées." });
    expect(text(at(19, 3, null))).toBe("Premières réponses : 3 sur 19 candidatures.");
    // 1 réponse contre 0 : pas « avance ».
    expect(text(at(19, 1, 0))).toBe("Premières réponses : 1 sur 19 candidatures.");
    expect(at(19, 5, 3)).toEqual({ before: "Ta recherche ", accent: "avance", after: " : plus de réponses qu'au trimestre d'avant." });
    expect(text(at(19, 3, 3))).toBe("Ta recherche tient le rythme : autant de réponses qu'au trimestre d'avant.");
    expect(text(at(19, 2, 3))).toBe("Ta recherche ralentit : moins de réponses qu'au trimestre d'avant.");
    expect(conclusion({ funnel: { received: 0, retained: 0, applications: 9, responses: 2, interviews: 0, engagements: 0 }, previous_responses: 4 } as Parameters<typeof conclusion>[0], "month").after).toBe(
      " : moins de réponses qu'au mois d'avant.",
    );
  });
});
