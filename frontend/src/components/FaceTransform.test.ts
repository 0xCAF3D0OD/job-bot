// Le personnage se transforme (docs/123, complément 0.96.0).
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FaceTransform from "./FaceTransform.vue";

function motion(reduce: boolean): void {
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: reduce && query.includes("reduce"), addEventListener() {}, removeEventListener() {} }));
}
afterEach(() => vi.unstubAllGlobals());

describe("FaceTransform", () => {
  it("chaque page a son objet : la loupe, la cloche, la cravate…", () => {
    motion(false);
    const cases = { offers: ".ft-loupe", alerts: ".ft-ring-bell", "orp-meeting": ".ft-tie", insights: ".ft-donut", settings: ".ft-gear", today: ".ft-rays", applications: ".ft-arrow", profile: ".ft-ring" } as const;
    for (const [kind, part] of Object.entries(cases)) {
      const svg = mount(FaceTransform, { props: { kind: kind as keyof typeof cases } }).find("svg");
      expect(svg.classes()).toContain(`ft-${kind}`);
      expect(svg.find(part).exists()).toBe(true);
      expect(svg.attributes("aria-hidden")).toBe("true");
    }
  });

  it("« réduire les animations » : le visage seul, sans objet", () => {
    motion(true);
    const svg = mount(FaceTransform, { props: { kind: "offers" } }).find("svg");
    expect(svg.classes()).toContain("ft-still");
    expect(svg.find(".ft-loupe").exists()).toBe(false);
    expect(svg.find(".ft-eye").exists()).toBe(true);
  });

  it("se joue une seule fois, jamais en boucle (WCAG 2.2.2)", () => {
    const css = readFileSync(join(__dirname, "..", "style.css"), "utf8");
    const rules = css.split("\n").filter((line) => /^\.ft-[^{]*\{[^}]*animation:/.test(line));
    expect(rules.length).toBeGreaterThan(0);
    for (const rule of rules) expect(rule).not.toMatch(/infinite/);
  });
});
