/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CountBadge from "./CountBadge.vue";

// Une seule pastille de nombre (1.6.33 ; NN/g, heuristique 4 « Cohérence et standards »).
describe("CountBadge", () => {
  it("accent par défaut, orange pour la cloche ; la place vient du parent", () => {
    const tab = mount(CountBadge, { props: { count: 4 }, attrs: { class: "tab-bar-count" } });
    expect(tab.classes()).toEqual(["count-badge", "accent", "tab-bar-count"]);
    expect(tab.text()).toBe("4");
    const bell = mount(CountBadge, { props: { count: "9+", tone: "orange" }, attrs: { class: "bell-badge" } });
    expect(bell.classes()).toEqual(["count-badge", "orange", "bell-badge"]);
  });

  it("un seul style : le contour de la couleur du fond, et rien ailleurs ne redessine une pastille", () => {
    const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const rules = [...css.matchAll(/([^{}]*)\{([^{}]*)\}/g)].map((m) => [m[1]!.trim(), m[2]!] as const);
    const base = rules.find(([sel]) => sel === ".count-badge");
    expect(base?.[1]).toMatch(/box-shadow:\s*0 0 0 2px var\(--surface\)/);
    // Les classes de place ne changent ni la couleur, ni la taille, ni le contour.
    const restyled = rules.filter(
      ([sel, body]) => /\.(tab-count|tab-bar-count|bell-badge)\b/.test(sel) && /(background|box-shadow|min-width|height|border-radius|color):/.test(body),
    );
    expect(restyled.map(([sel]) => sel)).toEqual([]);
    expect(css).not.toMatch(/\.icon-badge|\.nav-count/);
  });
});
