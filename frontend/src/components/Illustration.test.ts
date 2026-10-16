import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import Illustration from "./Illustration.vue";

describe("Illustration (docs/67)", () => {
  it("pose l'image réduite, chargée à l'affichage, décorative par défaut", async () => {
    const plain = mount(Illustration, { props: { name: "bilan" } });
    const img = plain.find("img");
    expect(img.attributes("srcset")).toMatch(/bilan-480\.webp 480w$/);
    expect(img.attributes("loading")).toBe("lazy");
    expect(img.attributes("alt")).toBe("");
    expect(plain.attributes("aria-hidden")).toBe("true");
    // Pas de série sombre pour l'instant : la claire, assombrie par la feuille de style.
    expect(plain.find("source").exists()).toBe(false);
    expect(plain.classes()).toContain("no-dark");
    // L'entrée en fondu attend que l'image soit là.
    expect(plain.classes()).not.toContain("loaded");
    await img.trigger("load");
    expect(plain.classes()).toContain("loaded");

    const told = mount(Illustration, { props: { name: "bilan", label: "Bilan" } });
    expect(told.attributes("role")).toBe("img");
    expect(told.attributes("aria-label")).toBe("Bilan");
  });

  it("propose la version de 800 px pour les grandes", () => {
    const big = mount(Illustration, { props: { name: "porte-ouverte" } });
    expect(big.find("img").attributes("srcset")).toMatch(/porte-ouverte-480\.webp 480w, .*porte-ouverte-800\.webp 800w$/);
  });
});
