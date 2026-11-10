import { describe, expect, it } from "vitest";

import { shortCompany } from "./useAssistant";

// Le nom d'entreprise dans une pastille de l'Assistant (MODIFICATIONS du 8 novembre au soir, lot 16.1).
describe("shortCompany", () => {
  it("garde la partie après « - »", () => {
    expect(shortCompany("Comité international de la Croix-Rouge - ICRC")).toBe("ICRC");
  });
  it("sinon coupe à 24 caractères avec « … »", () => {
    expect(shortCompany("Banque Cantonale Vaudoise Services SA")).toBe("Banque Cantonale Vaudois…");
    expect(shortCompany("Alpstack")).toBe("Alpstack");
  });
  it("un trait d’union dans un mot ne coupe pas", () => {
    expect(shortCompany("Croix-Rouge")).toBe("Croix-Rouge");
  });
});
