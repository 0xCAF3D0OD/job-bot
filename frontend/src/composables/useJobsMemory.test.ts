import { afterEach, describe, expect, it } from "vitest";

import { useJobsMemory } from "./useJobsMemory";

afterEach(() => localStorage.clear());

describe("retour à la candidature commencée", () => {
  it("retient la dernière page de la rubrique, oublie la préparation une fois envoyée", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/offres/12/preparer");
    memory.remember("/actualites"); // hors rubrique : ignoré
    expect(memory.last.value).toBe("/candidatures/offres/12/preparer");
    expect(localStorage.getItem("jobbot-candidatures")).toBe("/candidatures/offres/12/preparer");
    memory.sent(99); // autre offre : rien ne change
    expect(memory.last.value).toBe("/candidatures/offres/12/preparer");
    memory.sent(12);
    expect(memory.last.value).toBe("/candidatures/suivi");
    memory.remember("/candidatures/preuves?mois=2026-09");
    expect(memory.last.value).toBe("/candidatures/preuves?mois=2026-09");
  });
});
