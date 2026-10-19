import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AssistantMascot from "./AssistantMascot.vue";
import BrandMark from "./BrandMark.vue";

describe("Le logo et la mascotte (docs/97)", () => {
  it("le logo : deux boucles et l'étoile, le trait plus épais quand il rapetisse", () => {
    const big = mount(BrandMark, { props: { size: 160 } });
    expect(big.findAll(".brand-logo-loop")).toHaveLength(2);
    expect(big.find(".brand-logo-star").exists()).toBe(true);
    expect(big.find(".brand-logo-loop").attributes("stroke-width")).toBe("2.6");
    expect(mount(BrandMark, { props: { size: 26 } }).find(".brand-logo-loop").attributes("stroke-width")).toBe("5");
    expect(mount(BrandMark, { props: { size: 16 } }).find(".brand-logo-loop").attributes("stroke-width")).toBe("7");
    expect(big.attributes("aria-hidden")).toBe("true");
  });

  it("la mascotte : le visage, l'œil, l'étoile, le sourire ; les traits s'épaississent", () => {
    const big = mount(AssistantMascot, { props: { size: 150 } });
    expect(big.find(".mascot-face").exists()).toBe(true);
    expect(big.findAll(".mascot-line")).toHaveLength(2);
    expect(big.find(".mascot-star").exists()).toBe(true);
    expect(big.find(".mascot-line").attributes("stroke-width")).toBe("4.42");
    expect(mount(AssistantMascot, { props: { size: 16 } }).find(".mascot-line").attributes("stroke-width")).toBe("10.8");
  });
});
