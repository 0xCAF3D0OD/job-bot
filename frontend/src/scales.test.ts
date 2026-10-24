/// <reference types="node" />
// Le garde-fou des échelles (docs/135 §7, 1.6.12) : dans les styles, un espacement, une taille de
// texte, un rayon, une graisse ou un interligne passe par une variable des échelles. Les seules
// valeurs en dur admises sont listées ici, chacune avec sa raison.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = resolve(process.cwd(), "src");

const PROPS =
  /(?<![\w-])((?:padding|margin)(?:-[a-z-]+)?|gap|row-gap|column-gap|font-size|font-weight|line-height|border(?:-(?:top|bottom)-(?:left|right))?-radius)\s*:\s*([^;]+)/g;

// Hors échelle par décision (docs/135 §1 et §6, Écarts 1.6.11) : la règle entière.
const EXEMPT_RULES: [RegExp, string][] = [
  [/(^|[\s,])\.(letter|cv|orp-sheet)[\w-]*|(^|[\s,])\.kw\b/, "lettre, CV et feuille ORP : ils imitent le papier et le PDF"],
  [/#print-root|(^|[\s,])\.orp-(holder|sign)\b/, "la feuille ORP imprimée, en millimètres et en points"],
  [/(^|[\s,])\.(dmock|confetti)\b/, "illustrations : la maquette de « La plateforme », les confettis"],
  [/\.hover-note-info\b/, "marges négatives qui compensent la cible de 2,75 rem du bouton d'aide"],
  [/^input, select, textarea$/, "16 px : en dessous, l'iPhone zoome sur le champ"],
  [/^\.info-card \.summary-rows$/, "la place réservée au bouton de la carte"],
];

// Valeurs admises partout : variables, zéro, bordures d'un pixel, unités relatives, calculs
// (réserves de place autour d'un élément fixe), mots-clés.
const ALLOWED_TOKEN =
  /^(var\(.+\)|calc\(.+\)|max\(.+\)|min\(.+\)|clamp\(.+\)|env\(.+\)|-?0|-?1px|-?\d*\.?\d+(em|%|vw|vh|lh)|auto|inherit|initial|unset|normal|none|!important)$/;

// Réserves de place autour du dessin de la carte de réussite (marges de 9 et 11 rem).
const RESERVED: [RegExp, RegExp][] = [[/^\.success-card$/, /^(margin|margin-top)$/]];

function styleFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return styleFiles(path);
    return name.endsWith(".css") || name.endsWith(".vue") ? [path] : [];
  });
}

function rules(path: string): [string, string][] {
  let text = readFileSync(path, "utf8");
  if (path.endsWith(".vue")) text = [...text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join("\n");
  text = text.replace(/\/\*[\s\S]*?\*\//g, "");
  return [...text.matchAll(/([^{}]*)\{([^{}]*)\}/g)].map((m) => [m[1]!.trim().replace(/\s+/g, " "), m[2]!]);
}

// Découpe une valeur en morceaux, sans couper l'intérieur des parenthèses.
function tokens(value: string): string[] {
  const out: string[] = [];
  let depth = 0;
  let current = "";
  for (const char of value.trim()) {
    if (char === "(") depth++;
    if (char === ")") depth--;
    if (/\s/.test(char) && depth === 0) {
      if (current) out.push(current);
      current = "";
    } else current += char;
  }
  if (current) out.push(current);
  return out;
}

// À l'intérieur d'un calcul aussi, une longueur passe par une variable (1.6.12) : seuls ±1 px et
// les unités relatives restent admis ; les nombres sans unité (multiplicateurs) aussi.
function hardInside(token: string): string[] {
  if (!/^(calc|max|min|clamp)\(/.test(token)) return [];
  return (token.match(/-?\d*\.?\d+(rem|px)\b/g) ?? []).filter((length) => !/^-?1px$/.test(length));
}

function offenders(): string[] {
  const found: string[] = [];
  for (const file of styleFiles(SRC)) {
    for (const [selector, body] of rules(file)) {
      if (selector.startsWith("@") || selector.startsWith(":root")) continue;
      if (EXEMPT_RULES.some(([pattern]) => pattern.test(selector))) continue;
      for (const [, prop, value] of body.matchAll(PROPS)) {
        if (RESERVED.some(([sel, props]) => sel.test(selector) && props.test(prop!))) continue;
        const bad = tokens(value!).filter((token) => !ALLOWED_TOKEN.test(token) || hardInside(token).length > 0);
        if (bad.length) found.push(`${file.replace(SRC, "src")} « ${selector} » ${prop}: ${value!.trim()}`);
      }
    }
  }
  return found;
}

describe("Le garde-fou des échelles (docs/135, 1.6.12)", () => {
  it("aucun espacement, taille, rayon, graisse ni interligne en dur hors des exceptions", () => {
    expect(offenders()).toEqual([]);
  });

  it("le garde-fou trouve bien une valeur en dur, aussi dans un calcul", () => {
    const value = "0.9rem 1.5rem";
    expect(tokens(value).filter((token) => !ALLOWED_TOKEN.test(token))).toEqual(["0.9rem", "1.5rem"]);
    expect(tokens("var(--space-4) calc(var(--space-2) * -1)").every((token) => ALLOWED_TOKEN.test(token))).toBe(true);
    // Et à l'intérieur d'un calcul.
    expect(hardInside("calc(5.5rem + env(safe-area-inset-bottom))")).toEqual(["5.5rem"]);
    expect(hardInside("calc(var(--dock-h) + env(safe-area-inset-bottom))")).toEqual([]);
    expect(hardInside("calc(var(--space-2) * -1)")).toEqual([]);
  });
});
