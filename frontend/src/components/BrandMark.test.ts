import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AssistantMascot from "./AssistantMascot.vue";
import BrandMark from "./BrandMark.vue";

describe("Le logo et la mascotte (docs/97)", () => {
  it("le logo : deux boucles et le diamant en contour ; sous 24 px, une seule boucle (docs/98)", () => {
    const big = mount(BrandMark, { props: { size: 150 } });
    expect(big.findAll(".brand-logo-loop")).toHaveLength(2);
    expect(big.find(".brand-logo-loop").attributes("stroke-width")).toBe("2.6");
    expect(big.find(".brand-logo-diamond").attributes("stroke-width")).toBe("2.86");
    const bar = mount(BrandMark, { props: { size: 28 } });
    expect(bar.findAll(".brand-logo-loop")).toHaveLength(2);
    expect(bar.find(".brand-logo-loop").attributes("stroke-width")).toBe("5");
    const tab = mount(BrandMark, { props: { size: 16 } });
    expect(tab.findAll(".brand-logo-loop")).toHaveLength(1);
    expect(tab.find(".brand-logo-diamond").attributes("stroke-width")).toBe("11");
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
