import { describe, expect, it } from "vitest";

import { WHY_MAX, whyLine } from "./whyLine";

describe("la phrase « pourquoi » du tri", () => {
  it("une phrase courte reste telle quelle", () => {
    expect(whyLine("Ta plateforme colle.")).toBe("Ta plateforme colle.");
  });

  it("une phrase longue garde sa première phrase", () => {
    const text = "Ton expérience Kubernetes colle au poste. Il demande aussi Go et trois ans de Terraform en production.";
    expect(whyLine(text)).toBe("Ton expérience Kubernetes colle au poste.");
  });

  it("sans fin de phrase, coupe à la virgule ou au mot, jamais de « … »", () => {
    const text = "Ton expérience Kubernetes et Terraform colle au poste, mais il demande aussi Go et un permis de conduire";
    expect(whyLine(text)).toBe("Ton expérience Kubernetes et Terraform colle au poste.");
    const words = "un ".repeat(40).trim();
    const line = whyLine(words);
    expect(line.length).toBeLessThanOrEqual(WHY_MAX);
    expect(line).not.toContain("…");
    expect(line.endsWith("un.")).toBe(true);
  });

  it("80 caractères au plus, point compris", () => {
    const text = "Plateforme cloud, CI/CD et observabilité : trois points forts de ton parcours qui comptent pour ce poste de lead";
    const line = whyLine(text);
    expect(line.length).toBeLessThanOrEqual(WHY_MAX);
    expect(line).not.toMatch(/[,;:]\.$/);
  });
});
