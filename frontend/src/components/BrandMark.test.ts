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

  it("la mascotte (docs/99) : un visage rond, trois expressions ; les traits s'épaississent", () => {
    const listening = mount(AssistantMascot, { props: { size: 150 } });
    expect(listening.attributes("data-mood")).toBe("listening");
    expect(listening.find(".mascot-face").exists()).toBe(true);
    expect(listening.findAll(".mascot-line")).toHaveLength(2);
    expect(listening.findAll(".mascot-star")).toHaveLength(1);
    expect(listening.find(".mascot-line").attributes("stroke-width")).toBe("6.5");
    expect(mount(AssistantMascot, { props: { size: 16 } }).find(".mascot-line").attributes("stroke-width")).toBe("10.8");

    const thinking = mount(AssistantMascot, { props: { size: 150, mood: "thinking" } });
    expect(thinking.findAll(".mascot-dot")).toHaveLength(2);
    expect(thinking.findAll(".mascot-line")).toHaveLength(1);
    expect(thinking.find(".mascot-star").exists()).toBe(false);

    const found = mount(AssistantMascot, { props: { size: 150, mood: "found" } });
    expect(found.findAll(".mascot-star")).toHaveLength(2);
    expect(found.find(".mascot-mouth").exists()).toBe(true);
    expect(found.find(".mascot-line").exists()).toBe(false);
    expect(found.attributes("aria-hidden")).toBe("true");
  });
});
