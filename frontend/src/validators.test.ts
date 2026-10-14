import { describe, expect, it } from "vitest";

import { email, futureOrToday, postcode, secureAddress, senders, webAddress } from "./validators";

describe("vérification au fil de la saisie (docs/29 §4)", () => {
  it("accepte le vide (champ facultatif) et les bonnes valeurs", () => {
    for (const check of [postcode, email, webAddress, secureAddress]) expect(check("")).toBeNull();
    expect(postcode(" 1020 ")).toBeNull();
    expect(email("camille@exemple.ch")).toBeNull();
    expect(webAddress("linkedin.com/in/camille")).toBeNull();
    expect(webAddress("https://exemple.ch")).toBeNull();
    expect(secureAddress("https://www.jobscout24.ch")).toBeNull();
    expect(senders("alerts@jobs.ch jobscout24.ch")).toBeNull();
    expect(futureOrToday("2026-10-14")("2026-10-20")).toBeNull();
  });

  it("explique ce qui ne va pas", () => {
    expect(postcode("10200")).toContain("Quatre chiffres");
    expect(email("camille@")).toContain("adresse complète");
    expect(webAddress("pas une adresse")).toContain("adresse web");
    expect(secureAddress("http://exemple.ch")).toContain("https://");
    expect(senders("")).toContain("Au moins");
    expect(senders("jobs")).toContain("« jobs »");
    expect(futureOrToday("2026-10-14")("2026-10-01")).toContain("à venir");
  });
});
