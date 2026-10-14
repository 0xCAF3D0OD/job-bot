import { describe, expect, it } from "vitest";

import { fromQuery, toQuery, DEFAULT_FILTERS } from "./composables/useOfferFilters";
import { remoteText } from "./format";

describe("télétravail (docs/26)", () => {
  it("rédige l'étiquette de la carte", () => {
    expect(remoteText({ remote: "hybrid", remote_days: 2 })).toBe("Télétravail 2 j");
    expect(remoteText({ remote: "hybrid" })).toBe("Télétravail partiel");
    expect(remoteText({ remote: "full", remote_region: "Europe" })).toBe("100 % télétravail · Europe");
    expect(remoteText({ remote: "full" })).toBe("100 % télétravail");
    expect(remoteText({ remote: "onsite" })).toBeNull();
    expect(remoteText({})).toBeNull();
  });

  it("garde le filtre dans l'adresse", () => {
    expect(toQuery({ ...DEFAULT_FILTERS, remote: "partial" })).toEqual({ teletravail: "partiel" });
    expect(fromQuery({ teletravail: "complet" }).remote).toBe("full");
    expect(fromQuery({ teletravail: "n'importe" }).remote).toBeNull();
  });
});
