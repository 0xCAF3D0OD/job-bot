/// <reference types="node" />
// Les variables de l'identité (docs/139) : docs/mobile/tokens.css est la source de vérité ; style.css reprend
// chaque valeur telle quelle, en clair comme en sombre, avec les mêmes noms de rôles.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

// Lancé depuis frontend/ (npm test, vitest).
const reference = readFileSync(resolve(process.cwd(), "../docs/mobile/tokens.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

// Ce que le projet a déjà sous un autre nom : la police (Figtree Variable, servie par l'app) ; la police
// manuscrite arrive avec le trait crayon (onboarding, objectif atteint).
const NOT_COPIED = new Set(["font", "font-hand"]);

function declarations(block: string): Map<string, string> {
  const found = new Map<string, string>();
  for (const match of block.matchAll(/--([\w-]+):\s*([^;]+);/g)) {
    if (!found.has(match[1]!)) found.set(match[1]!, match[2]!.trim());
  }
  return found;
}

function block(text: string, start: number): string {
  let depth = 0;
  for (let i = text.indexOf("{", start); i < text.length; i++) {
    if (text[i] === "{") depth++;
    if (text[i] === "}" && --depth === 0) return text.slice(start, i + 1);
  }
  return text.slice(start);
}

const referenceLight = declarations(block(reference, reference.indexOf(":root {")));
const referenceDark = declarations(block(reference, reference.indexOf("@media (prefers-color-scheme: dark)")));
const darkBlock = block(css, css.indexOf("@media (prefers-color-scheme: dark)"));
const styleDark = declarations(darkBlock);
const styleLight = declarations(css.replace(darkBlock, ""));
const normalize = (value: string) => value.replace(/\s+/g, " ").toLowerCase();

describe("les variables de docs/mobile/tokens.css (docs/139)", () => {
  it("chaque valeur claire est reprise telle quelle dans style.css", () => {
    expect(referenceLight.size).toBeGreaterThan(40);
    for (const [name, value] of referenceLight) {
      if (NOT_COPIED.has(name)) continue;
      expect(styleLight.get(name) && normalize(styleLight.get(name)!), `--${name}`).toBe(normalize(value));
    }
  });

  it("chaque valeur sombre est reprise telle quelle dans le premier bloc sombre de style.css", () => {
    expect(referenceDark.size).toBeGreaterThan(20);
    for (const [name, value] of referenceDark) {
      expect(styleDark.get(name) && normalize(styleDark.get(name)!), `--${name}`).toBe(normalize(value));
    }
  });

  it("« À creuser » reste en gris chaud, jamais l'orange (D5, 2026-11-02)", () => {
    expect(styleLight.get("score-dig")).not.toBe(styleLight.get("warning"));
    expect(styleDark.get("score-dig")).not.toBe(styleDark.get("warning"));
  });
});
