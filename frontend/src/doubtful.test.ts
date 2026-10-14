import { describe, expect, it } from "vitest";

import { activeCount, DEFAULT_FILTERS, fromQuery, toQuery } from "./composables/useOfferFilters";

describe("offres à vérifier (docs/30 §3)", () => {
  it("garde « Masquer les offres à vérifier » dans l'adresse, éteint par défaut", () => {
    expect(DEFAULT_FILTERS.hideDoubtful).toBe(false);
    expect(toQuery({ ...DEFAULT_FILTERS, hideDoubtful: true })).toEqual({ verifier: "masquer" });
    expect(fromQuery({ verifier: "masquer" }).hideDoubtful).toBe(true);
    expect(fromQuery({}).hideDoubtful).toBe(false);
    expect(activeCount({ ...DEFAULT_FILTERS, hideDoubtful: true })).toBe(1);
  });
});
