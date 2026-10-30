/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { grow } from "./useAutoGrow";

describe("zones de texte (planche « Champs »)", () => {
  it("pas de poignée : elles s'agrandissent seules", () => {
    const css = readFileSync(resolve(__dirname, "../style.css"), "utf8");
    expect(css).toMatch(/\ntextarea \{[^}]*resize: none;[^}]*field-sizing: content;/);
    expect(css).not.toMatch(/textarea[^{]*\{[^}]*resize: (vertical|both|horizontal)/);
  });

  it("sans field-sizing, la hauteur suit le contenu", () => {
    const area = document.createElement("textarea");
    Object.defineProperty(area, "scrollHeight", { value: 180 });
    grow(area);
    expect(area.style.height).toBe("180px");
  });
});
