import { describe, expect, it } from "vitest";

import { activeChips, activeCount, DEFAULT_FILTERS, fromQuery, toQuery } from "./composables/useOfferFilters";

describe("offres à vérifier (docs/30 §3)", () => {
  it("garde « Masquer les offres à vérifier » dans l’adresse, éteint par défaut", () => {
    expect(DEFAULT_FILTERS.hideDoubtful).toBe(false);
    expect(toQuery({ ...DEFAULT_FILTERS, hideDoubtful: true })).toEqual({ verifier: "masquer" });
    expect(fromQuery({ verifier: "masquer" }).hideDoubtful).toBe(true);
    expect(fromQuery({}).hideDoubtful).toBe(false);
    expect(activeCount({ ...DEFAULT_FILTERS, hideDoubtful: true })).toBe(1);
  });
});

describe("filtre « Note » : sûres ou provisoires (PR 26)", () => {
  it("garde le choix dans l’adresse, compte pour un filtre et a sa pastille", () => {
    expect(DEFAULT_FILTERS.basis).toBeNull();
    expect(toQuery({ ...DEFAULT_FILTERS, basis: "provisional" })).toEqual({ base: "provisoire" });
    expect(toQuery({ ...DEFAULT_FILTERS, basis: "sure" })).toEqual({ base: "sure" });
    expect(fromQuery({ base: "provisoire" }).basis).toBe("provisional");
    expect(fromQuery({ base: "sure" }).basis).toBe("sure");
    expect(fromQuery({ base: "autre" }).basis).toBeNull();
    expect(activeCount({ ...DEFAULT_FILTERS, basis: "sure" })).toBe(1);
    expect(activeChips({ ...DEFAULT_FILTERS, basis: "provisional" })).toEqual([{ key: "basis", label: "Notes provisoires", patch: { basis: null } }]);
    expect(activeChips({ ...DEFAULT_FILTERS, basis: "sure" })[0]?.label).toBe("Notes sûres");
  });
});
