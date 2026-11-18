import { describe, expect, it } from "vitest";

import { activeChips, activeCount, basisChoices, contractCount, DEFAULT_FILTERS, fromQuery, RATE_CHOICES, SCORE_CHOICES, scoreLabel, toggleContract, toQuery } from "./useOfferFilters";

// Section 31 du 16.11 : des libellés compris sans connaître jobA1, mêmes seuils et mêmes clés qu'avant.
describe("filtres des offres : libellés compréhensibles (section 31)", () => {
  it("Note minimale sur 100 : Toutes / 50 et + / 75 et + / 85 et +, aux seuils des mots de la note", () => {
    expect(SCORE_CHOICES).toEqual([
      { label: "Toutes", min: null },
      { label: "50 et +", min: 50 },
      { label: "75 et +", min: 75 },
      { label: "85 et +", min: 85 },
    ]);
    expect(scoreLabel({ minScore: 75, maxScore: null })).toBe("75 et +");
    // Une adresse d'avant (?note=60-90) garde ses bornes.
    expect(scoreLabel({ minScore: 60, maxScore: 90 })).toBe("60–90");
  });

  it("Taux d’activité : Tous / Dès 60 % / Dès 80 % / 100 %, mêmes valeurs", () => {
    expect(RATE_CHOICES).toEqual([
      { label: "Tous", value: null },
      { label: "Dès 60 %", value: 60 },
      { label: "Dès 80 %", value: 80 },
      { label: "100 %", value: 100 },
    ]);
  });

  it("Type de note : « Définitives » remplace « Sûres », mêmes compteurs", () => {
    expect(basisChoices({ sure: 104, provisional: 312 }).map((c) => c.label)).toEqual(["Toutes", "Définitives · 104", "Provisoires · 312"]);
  });

  it("les pastilles des filtres actifs reprennent les mêmes mots", () => {
    const labels = activeChips({ ...DEFAULT_FILTERS, minScore: 85, basis: "sure", remote: "partial", minRate: 80 }).map((c) => c.label);
    expect(labels).toEqual(["Note 85 et +", "Notes définitives", "Télétravail possible, même partiel", "Taux dès 80 %"]);
    expect(activeChips({ ...DEFAULT_FILTERS, minRate: 100 })[0]?.label).toBe("Taux 100 %");
    expect(activeChips({ ...DEFAULT_FILTERS, remote: "full" })[0]?.label).toBe("Télétravail complet");
  });

  it("les filtres déjà enregistrés restent valides : mêmes clés et valeurs dans l’adresse", () => {
    const query = { note: "75", taux: "80", base: "sure", teletravail: "partiel", tri: "score" };
    const filters = fromQuery(query);
    expect(filters).toMatchObject({ minScore: 75, maxScore: null, minRate: 80, basis: "sure", remote: "partial", sort: "score" });
    expect(toQuery(filters)).toEqual(query);
    expect(activeCount(filters)).toBe(4);
  });
});

// Issue 468 (Kevin, 18.11) : le filtre Contrat, plusieurs choix, « Non précisé » compris.
describe("filtre Contrat", () => {
  it("l’adresse garde les contrats cochés, dans l’ordre des choix", () => {
    const filters = fromQuery({ contrat: ["non_precise", "cdi"] });
    expect(filters.contracts).toEqual(["cdi", "non_precise"]);
    expect(toQuery(filters)).toEqual({ contrat: ["cdi", "non_precise"] });
    expect(activeCount(filters)).toBe(2);
    expect(activeChips(filters).map((c) => c.label)).toEqual(["Contrat : CDI", "Contrat : Non précisé"]);
    expect(activeChips(filters)[0]?.patch).toEqual({ contracts: ["non_precise"] });
  });

  it("une valeur inconnue est ignorée : elle ne vide jamais la liste sans le dire", () => {
    expect(fromQuery({ contrat: ["apprentissage", "xyz"] }).contracts).toEqual([]);
    expect(fromQuery({ contrat: ["apprentissage", "cdd"] }).contracts).toEqual(["cdd"]);
    expect(activeCount(fromQuery({ contrat: "apprentissage" }))).toBe(0);
  });

  it("cocher et décocher ; le nombre de chaque contrat vient du serveur, 0 s’il manque", () => {
    expect(toggleContract([], "stage")).toEqual(["stage"]);
    expect(toggleContract(["cdi", "stage"], "cdi")).toEqual(["stage"]);
    expect(toggleContract(["stage"], "cdi")).toEqual(["cdi", "stage"]);
    const facets = { contracts: [{ value: "cdi", count: 120 }, { value: "stage", count: 0 }] };
    expect(contractCount(facets, "cdi")).toBe(120);
    expect(contractCount(facets, "stage")).toBe(0);
    expect(contractCount({}, "cdd")).toBe(0);
    expect(DEFAULT_FILTERS.contracts).toEqual([]);
  });
});

describe("Filtre « Distance » dans l’adresse (issue 468)", () => {
  it("?distance=30 et ?distance=inconnu ; une valeur inconnue est ignorée, jamais une liste vidée sans le dire", () => {
    expect(fromQuery({ distance: "30" }).distance).toBe("30");
    expect(fromQuery({ distance: "inconnu" }).distance).toBe("unknown");
    expect(fromQuery({ distance: "20" }).distance).toBeNull();
    expect(toQuery({ ...DEFAULT_FILTERS, distance: "unknown" }).distance).toBe("inconnu");
    expect(activeCount({ ...DEFAULT_FILTERS, distance: "15" })).toBe(1);
  });
});
