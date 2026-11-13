// Contrôle final du récapitulatif du 11 novembre (PR 43) : aucun champ ovale (rayon de 20 px ou plus) dans les
// panneaux et les formulaires. Les champs des maquettes ont des coins de 12 (ou de 8 pour la saisie de la date).
import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = resolve(__dirname);
const files = ["style.css", ...["components", "views"].flatMap((dir) => readdirSync(join(SRC, dir)).filter((name) => name.endsWith(".vue")).map((name) => join(dir, name)))];
const sources: Record<string, string> = Object.fromEntries(files.map((file) => [file, readFileSync(join(SRC, file), "utf8")]));

// Une règle qui vise un champ de saisie et lui donne un rayon de capsule ou de 20 px et plus.
const RULE = /([^{}]*\b(?:input|textarea|select)\b[^{}]*)\{([^}]*)\}/g;
const OVAL = /border-radius:\s*(?:var\(--radius-pill\)|var\(--space-5\)|999px|50%|(?:[2-9]\d|\d{3,})px|(?:1\.2[5-9]|1\.[3-9]\d*|[2-9](?:\.\d+)?)rem)/;
// Ce qui n'est pas un champ de saisie : les boutons radio et les cases, ronds par nature.
const ROUND_BY_NATURE = /radio|checkbox|choice-rad|answer-mode|switch|toggle|range/;
// Hors des panneaux et des formulaires, la capsule reste : la règle de base des champs (barres d'outils), la zone de
// texte de base, la liste compacte et les recherches. La règle `SCOPED` les ramène à 12 dans un panneau ou un formulaire.
const OUTSIDE = [/^:is\(input:is\(\[type="text"\].*\):not\(:where\(\.composer \*\)\)$/, /^textarea$/, /^select\.field-compact$/, /search/];
const SCOPED =
  ':where(dialog, form, [role="dialog"], .side-panel) :is(input:not([type="search"], [type="checkbox"], [type="radio"], [type="range"], [type="file"], [type="color"]), select, textarea):not(:where(.composer *)) { border-radius: var(--ff-radius); }';

describe("coins des champs (PR 43)", () => {
  it("aucune règle ne rend un champ ovale, hors la base des barres d'outils et les recherches", () => {
    const found: string[] = [];
    for (const [path, source] of Object.entries(sources)) {
      const css = path.endsWith(".vue") ? [...source.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join("\n") : source;
      for (const [, selector, body] of css.replace(/\/\*[\s\S]*?\*\//g, "").matchAll(RULE)) {
        const name = selector!.trim();
        if (!OVAL.test(body!) || ROUND_BY_NATURE.test(name) || OUTSIDE.some((allowed) => allowed.test(name))) continue;
        found.push(`${path} « ${name} »`);
      }
    }
    expect(found).toEqual([]);
  });

  it("dans un panneau ou un formulaire, champs, listes et zones de texte ont les coins de 12", () => {
    expect(sources["style.css"]).toContain(SCOPED);
    expect(sources["style.css"]).toContain("--ff-radius: 12px");
  });
});
