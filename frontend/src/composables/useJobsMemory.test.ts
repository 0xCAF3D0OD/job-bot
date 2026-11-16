import { afterEach, describe, expect, it, vi } from "vitest";

import { useJobsMemory } from "./useJobsMemory";

afterEach(() => localStorage.clear());

describe("dernière page de Candidatures", () => {
  it("retient l’onglet quitté, rien hors de la rubrique", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/suivi?candidature=4");
    memory.remember("/actualites");
    expect(memory.last.value).toBe("/candidatures/suivi?candidature=4");
    expect(localStorage.getItem("jobbot-candidatures")).toBe("/candidatures/suivi?candidature=4");
    expect(memory.menuLink("/aujourdhui")).toBe("/candidatures/suivi?candidature=4");
  });
});

describe("pages jamais retenues (lot 11.4, 13.11.2026)", () => {
  it("Mes alertes, Préparer et Relances ne sont pas retenues", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/offres");
    for (const path of [
      "/candidatures/alertes",
      "/candidatures/alertes?ajouter=1",
      "/candidatures/offres/12/preparer",
      "/candidatures/offres/12/preparer?doc=postuler",
      "/candidatures/relances",
    ]) memory.remember(path);
    expect(memory.last.value).toBe("/candidatures/offres");
  });

  it("depuis Préparer et Relances, le menu mène à la liste des offres", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/suivi");
    expect(memory.menuLink("/candidatures/offres/12/preparer")).toBe("/candidatures/offres");
    expect(memory.menuLink("/candidatures/relances")).toBe("/candidatures/offres");
    expect(memory.menuLink("/candidatures/alertes")).toBe("/candidatures/suivi");
  });
});

describe("Trier n’est pas retenue (Kevin, 16.11.2026)", () => {
  it("après le tri, le menu mène à la dernière page de la rubrique, pas au tri", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/suivi");
    memory.remember("/candidatures/trier");
    expect(memory.last.value).toBe("/candidatures/suivi");
    expect(localStorage.getItem("jobbot-candidatures")).toBe("/candidatures/suivi");
    expect(memory.menuLink("/aujourdhui")).toBe("/candidatures/suivi");
  });

  it("depuis Trier, le menu mène à la liste des offres", () => {
    const memory = useJobsMemory();
    memory.remember("/candidatures/suivi");
    expect(memory.menuLink("/candidatures/trier")).toBe("/candidatures/offres");
  });

  it("un tri déjà retenu dans ce navigateur n’est plus repris", async () => {
    localStorage.setItem("jobbot-candidatures", "/candidatures/trier");
    vi.resetModules();
    const fresh = await import("./useJobsMemory");
    expect(fresh.useJobsMemory().last.value).toBe("/candidatures/offres");
  });
});
