/// <reference types="node" />
// Le garde-fou du mouvement des éléments (Kevin, 19.11.2026 ; docs/mouvement.md) : les valeurs de la décision,
// seulement l'opacité et la transformation, et un mouvement réduit en fondu de 150 ms sans déplacement ni cascade.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/motion.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
const base = css.slice(0, css.indexOf("@media (prefers-reduced-motion: reduce)"));

function value(block: string, name: string): string | undefined {
  return new RegExp(`${name}:\\s*([^;]+);`).exec(block)?.[1]?.trim();
}

describe("le mouvement des éléments (docs/mouvement.md)", () => {
  it("reprend les valeurs de la décision", () => {
    expect(value(base, "--motion-enter")).toBe("320ms cubic-bezier(0.05, 0.7, 0.1, 1)");
    expect(value(base, "--motion-exit")).toBe("180ms cubic-bezier(0.3, 0, 0.8, 0.15)");
    expect(value(base, "--motion-stagger")).toBe("40ms");
    expect(value(base, "--motion-sheet")).toBe("300ms cubic-bezier(0.05, 0.7, 0.1, 1)");
    expect(value(base, "--motion-sheet-exit")).toBe("200ms cubic-bezier(0.3, 0, 0.8, 0.15)");
    expect(value(base, "--motion-step-exit")).toBe("150ms cubic-bezier(0.3, 0, 0.8, 0.15)");
    expect(value(base, "--motion-progress")).toBe("300ms cubic-bezier(0.2, 0, 0, 1)");
    expect([value(base, "--motion-rise"), value(base, "--motion-sink"), value(base, "--motion-sheet-rise")]).toEqual(["8px", "4px", "24px"]);
  });

  it("en mouvement réduit : fondu de 150 ms, sans déplacement ni cascade", () => {
    for (const name of ["--motion-enter", "--motion-exit", "--motion-sheet", "--motion-sheet-exit", "--motion-scrim", "--motion-step-exit"]) {
      expect(value(reduced, name), name).toBe("150ms linear");
    }
    for (const name of ["--motion-stagger", "--motion-progress", "--motion-rise", "--motion-sink", "--motion-sheet-rise"]) {
      expect(value(reduced, name), name).toMatch(/^0(ms|px)$/);
    }
  });

  it("n'anime que l'opacité et la transformation", () => {
    const frames = [...css.matchAll(/@keyframes [\w-]+ \{([^{}]*\{[^{}]*\})+\s*\}/g)].map((m) => m[0]);
    expect(frames.length).toBeGreaterThan(0);
    for (const frame of frames) {
      const props = [...frame.matchAll(/([a-z-]+)\s*:/g)].map((m) => m[1]);
      expect(props.every((p) => p === "opacity" || p === "transform"), frame).toBe(true);
    }
    for (const t of css.matchAll(/transition:\s*([^;]+);/g)) expect(t[1]).toMatch(/^transform /);
  });

  it("la cascade porte au plus sur 5 éléments", () => {
    expect(css).toContain("min(var(--motion-i, 0), 4)");
    expect(css).toContain(".motion-cascade > :nth-child(n + 5) { --motion-i: 4; }");
  });

  it("est chargé sur toutes les pages", () => {
    expect(readFileSync(resolve(process.cwd(), "src/main.ts"), "utf8")).toContain('import "./motion.css";');
  });
});
