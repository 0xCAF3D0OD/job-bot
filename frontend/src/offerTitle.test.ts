import { describe, expect, it } from "vitest";

import { displayTitle } from "./offerTitle";

describe("displayTitle (Q3, à l'affichage seulement)", () => {
  it("met un titre tout en majuscules en casse normale", () => {
    expect(displayTitle("INGÉNIEUR SYSTÈME")).toBe("Ingénieur système");
  });

  it("garde les sigles connus", () => {
    expect(displayTitle("INGÉNIEUR DEVOPS AWS (H/F)")).toBe("Ingénieur DevOps AWS (H/F)");
    expect(displayTitle("SRE - CI/CD ET KUBERNETES")).toBe("SRE - CI/CD et Kubernetes");
    expect(displayTitle("DÉVELOPPEUR .NET / C# SENIOR")).toBe("Développeur .NET / C# senior");
  });

  it("remplace « | » par « · »", () => {
    expect(displayTitle("Ingénieur DevOps | Lausanne")).toBe("Ingénieur DevOps · Lausanne");
    expect(displayTitle("CHEF DE PROJET IT | 80-100%")).toBe("Chef de projet IT · 80-100%");
  });

  it("rend leur capitale aux mots du lieu et de l'entreprise", () => {
    expect(displayTitle("TECHNICIEN SUPPORT LAUSANNE", { location: "Lausanne VD", company: "Acme SA" })).toBe(
      "Technicien support Lausanne",
    );
  });

  it("ne touche pas à la casse d'un titre déjà mixte", () => {
    expect(displayTitle("Ingénieur DEVOPS confirmé")).toBe("Ingénieur DEVOPS confirmé");
    expect(displayTitle("SAP Consultant")).toBe("SAP Consultant");
  });

  it("laisse un titre vide ou court", () => {
    expect(displayTitle(null)).toBe("");
    expect(displayTitle("QA")).toBe("QA");
  });
});
