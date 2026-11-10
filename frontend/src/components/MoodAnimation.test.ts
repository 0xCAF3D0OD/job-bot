import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import MoodAnimation, { type MoodKind } from "./MoodAnimation.vue";

// La maquette Animations (docs/139 étape 12) : chaque geste a sa forme, décorative.
describe("animations du logo", () => {
  const shapes: [MoodKind, string][] = [
    ["loupe", ".loupe"],
    ["cloche", ".arch"],
    ["hochement", ".triangle"],
    ["attente", ".spin"],
    ["envoyee", ".tilt"],
    ["objectif", ".sun"],
  ];
  it.each(shapes)("%s : sa forme, cachée aux lecteurs d’écran", (kind, shape) => {
    const svg = mount(MoodAnimation, { props: { kind } }).find("svg");
    expect(svg.attributes("aria-hidden")).toBe("true");
    expect(svg.attributes("data-mood-animation")).toBe(kind);
    expect(svg.find(shape).exists()).toBe(true);
  });

  it("le trait du logo garde son épaisseur, quelle que soit la forme", () => {
    for (const [kind] of shapes) {
      const lines = mount(MoodAnimation, { props: { kind } }).findAll("path.line");
      expect(lines.length).toBeGreaterThanOrEqual(2);
    }
  });
});
