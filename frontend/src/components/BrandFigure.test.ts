import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import BrandFigure, { FIGURES, figureAt } from "./BrandFigure.vue";

afterEach(() => vi.useRealTimers());

describe("BrandFigure (docs/68)", () => {
  it("un personnage par heure, le même pour tous à la même heure", () => {
    expect(FIGURES).toHaveLength(11);
    expect(figureAt(new Date(2026, 9, 17, 0, 5))).toBe(FIGURES[0]);
    expect(figureAt(new Date(2026, 9, 17, 13, 59))).toBe(FIGURES[2]);
    expect(figureAt(new Date(2026, 9, 18, 13, 0))).toBe(FIGURES[2]);
  });

  it("change à l'heure pile, et pose le dessin animé, décoratif", async () => {
    // Le dessin est chargé avant l'horloge simulée, avec une attente large : sous charge, sa
    // première préparation par Vite peut dépasser une seconde (docs/69 §5).
    await import(`../assets/personnages/${FIGURES[9]}.svg?raw`);
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "Date"] });
    vi.setSystemTime(new Date(2026, 9, 17, 9, 59, 30));
    const wrapper = mount(BrandFigure);
    expect(wrapper.attributes("data-figure")).toBe(FIGURES[9]);
    expect(wrapper.attributes("aria-hidden")).toBe("true");
    await vi.waitFor(
      async () => {
        await flushPromises();
        expect(wrapper.find("svg").exists()).toBe(true);
      },
      { timeout: 5000 },
    );
    await vi.advanceTimersByTimeAsync(31_000);
    expect(wrapper.attributes("data-figure")).toBe(FIGURES[10]);
  });
});
