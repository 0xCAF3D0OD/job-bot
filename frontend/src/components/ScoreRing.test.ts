// La note dans un cercle dont le contour se remplit comme la note (docs/73).
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ScoreRing from "./ScoreRing.vue";

describe("ScoreRing", () => {
  it("remplit le contour selon la note, et la dit en toutes lettres", () => {
    const ring = mount(ScoreRing, { props: { score: 75 } }).find("[data-test=score]");
    expect(ring.text()).toBe("75");
    expect(ring.attributes("style")).toContain("--p: 75");
    expect(ring.attributes("aria-label")).toBe("Note de l'IA : 75 sur 100");
    expect(ring.classes()).toContain("high");
  });

  it("garde le contour entre vide et plein, et signale une note ancienne", () => {
    const full = mount(ScoreRing, { props: { score: 130, stale: true } }).find("[data-test=score]");
    expect(full.attributes("style")).toContain("--p: 100");
    expect(full.attributes("aria-label")).toContain("ancien profil");
    expect(mount(ScoreRing, { props: { score: -5 } }).attributes("style")).toContain("--p: 0");
  });

  it("montre « /100 » dans le grand cercle du panneau", () => {
    expect(mount(ScoreRing, { props: { score: 42, large: true } }).text()).toBe("42/100");
  });
});
