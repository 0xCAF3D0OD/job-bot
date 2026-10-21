// Rien ne déborde sur le côté (0.82.2) : sur téléphone, un débordement (une infobulle au bord
// droit) élargissait tout l'écran et poussait l'assistant hors du cadre.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8");

describe("débordement sur le côté", () => {
  it("la page et son corps rognent ce qui dépasse, sans zone de défilement", () => {
    expect(css).toMatch(/html, body \{ overflow-x: clip; \}/);
  });

  it("sur écran tactile, l'infobulle d'un bouton icône ne prend pas de place", () => {
    expect(css).toMatch(
      /@media \(hover: none\) and \(pointer: coarse\) \{ button\.icon-only:not\(:focus-visible\)::after \{ display: none; \} \}/,
    );
  });
});
