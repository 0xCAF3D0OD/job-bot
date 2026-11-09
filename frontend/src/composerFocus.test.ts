import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// Lot 17 (MODIFICATIONS du 8 novembre au soir, §3) : dans le Composer, une seule forme visible au focus, la pilule.
const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8");

describe("Zone de saisie : un seul anneau, sur la pilule (lot 17)", () => {
  it("la règle de base des champs ne touche pas le champ du Composer", () => {
    const base = css.split("\n").filter((line) => line.startsWith(':is(input:is([type="text"]'));
    expect(base.length).toBeGreaterThan(0);
    for (const line of base) expect(line).toContain(":not(:where(.composer *))");
  });

  it("le focus est sur la pilule entière, jamais sur le champ intérieur", () => {
    expect(css).toMatch(/\.composer:focus-within \{ outline: 2px solid var\(--primary-graphic\); outline-offset: 1px; \}/);
    const inner = css.match(/\.composer \.composer-input \{[^}]*\}/)?.[0] ?? "";
    expect(inner).toContain("border: 0");
    expect(inner).toContain("background: transparent");
    expect(inner).toContain("outline: none");
  });

  it("aucune seconde pilule autour du Composer sur la page Assistant", () => {
    const page = css.match(/\.assistant-page \.assistant-form \{[^}]*\}/)?.[0] ?? "";
    expect(page).not.toMatch(/border-radius|background/);
  });

  it("Envoyer est un bouton plein (niveau 1)", () => {
    expect(css).toContain(".composer-send { background: var(--action); color: var(--on-action); }");
  });
});
