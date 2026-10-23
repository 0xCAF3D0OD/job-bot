/// <reference types="node" />
// Contraste du texte (docs/28 §2) : chaque couleur de texte du thème atteint 4,5:1 sur les
// fonds où elle s'affiche, en mode clair et en mode sombre.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

// Lancé depuis frontend/ (npm test, vitest).
const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8");

function tokens(block: string): Record<string, string> {
  const found: Record<string, string> = {};
  for (const match of block.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)) found[match[1]!] = match[2]!;
  return found;
}

const light = tokens(css.slice(css.indexOf(":root {"), css.indexOf("}", css.indexOf(":root {"))));
const darkStart = css.indexOf("@media (prefers-color-scheme: dark)");
const dark = { ...light, ...tokens(css.slice(darkStart, css.indexOf("}\n}", darkStart))) };

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const f = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * f(r!) + 0.7152 * f(g!) + 0.0722 * f(b!);
}

function ratio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi! + 0.05) / (lo! + 0.05);
}

function mix(color: string, base: string, share: number): string {
  const channel = (hex: string, i: number) => parseInt(hex.slice(i, i + 2), 16);
  return `#${[1, 3, 5]
    .map((i) => Math.round(channel(color, i) * share + channel(base, i) * (1 - share)).toString(16).padStart(2, "0"))
    .join("")}`;
}

// Textes et fonds où ils s'affichent ; les fonds teintés sont ceux des pastilles.
const TEXTS = ["text", "muted", "accent", "ok-text", "orange-text", "down-text"];
const BACKGROUNDS = ["bg", "band", "surface", "panel"];

describe.each([
  ["clair", light],
  ["sombre", dark],
])("mode %s", (_mode, theme) => {
  it.each(TEXTS)("--%s lisible sur les fonds de page", (text) => {
    for (const background of BACKGROUNDS) {
      expect(ratio(theme[text]!, theme[background]!), `${text} sur ${background}`).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("--faint, réservé à ce qui n'est pas du texte (docs/135, 1.6.1)", () => {
  it("au moins 3,3:1 en clair et 3:1 en sombre sur les fonds de page", () => {
    for (const background of BACKGROUNDS) {
      expect(ratio(light.faint!, light[background]!), `clair, ${background}`).toBeGreaterThanOrEqual(3.3);
      expect(ratio(dark.faint!, dark[background]!), `sombre, ${background}`).toBeGreaterThanOrEqual(3);
    }
  });

  it("seulement pour les chevrons, les soulignés et l'encre des dessins ; le texte gris est en --muted", () => {
    const rules = [...css.matchAll(/([^{}]+)\{([^{}]*var\(--faint\)[^{}]*)\}/g)].map((m) => m[1]!.trim());
    for (const selector of rules) expect(selector).toMatch(/^(\.disclosure-chevron|\.hover-note|\.drawing )/);
    expect(rules.length).toBeGreaterThan(0);
  });
});

describe("pastilles teintées (mode clair)", () => {
  it("le texte reste lisible sur sa teinte", () => {
    const white = light.surface!;
    const pairs: [string, string][] = [
      [light.accent!, light["accent-soft"]!],
      [light.accent!, mix(light.accent!, white, 0.15)],
      [light["orange-text"]!, mix(light.warn!, white, 0.18)],
      [light["orange-text"]!, light["orange-soft"]!],
      [light["ok-text"]!, mix(light.ok!, white, 0.16)],
      ["#ffffff", light.accent!],
    ];
    for (const [text, background] of pairs) expect(ratio(text, background), `${text} sur ${background}`).toBeGreaterThanOrEqual(4.5);
  });
});

describe("étiquettes orange (docs/135)", () => {
  it("le texte orange reste lisible sur son fond, en clair et en sombre", () => {
    expect(ratio(light["orange-text"]!, light["orange-soft"]!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(dark["orange-text"]!, dark["orange-soft"]!)).toBeGreaterThanOrEqual(4.5);
  });
});

describe("initiales des entreprises et pastille de la cloche (audit du 22.10.2026)", () => {
  it("l'initiale foncée sur les fonds clairs, le chiffre blanc sur un rouge assez sombre", () => {
    for (const tone of ["orange", "mint", "sky"]) {
      expect(css).toMatch(new RegExp(`\\.logo\\.c\\d \\{ background: var\\(--${tone}\\); color: #11111f; \\}`));
      expect(ratio("#11111f", light[tone]!)).toBeGreaterThanOrEqual(4.5);
    }
    expect(css).toContain("background: #c62a2f; color: #fff;");
    expect(ratio("#ffffff", "#c62a2f")).toBeGreaterThanOrEqual(4.5);
  });
});
