import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AssistantMascot from "./AssistantMascot.vue";
import BrandMark from "./BrandMark.vue";

describe("Le logo et la mascotte (docs/97)", () => {
  it("le logo (docs/100) : une boucle et le diamant au même trait ; plus épais à 32 px et moins", () => {
    const big = mount(BrandMark, { props: { size: 104 } });
    expect(big.findAll(".brand-logo-loop")).toHaveLength(1);
    expect(big.find(".brand-logo-loop").attributes("stroke-width")).toBe("3.6");
    expect(big.find(".brand-logo-diamond").attributes("stroke-width")).toBe("3.6");
    expect(mount(BrandMark, { props: { size: 48 } }).find(".brand-logo-loop").attributes("stroke-width")).toBe("5.5");
    const bar = mount(BrandMark, { props: { size: 28 } });
    expect(bar.findAll(".brand-logo-loop")).toHaveLength(1);
    expect(bar.find(".brand-logo-loop").attributes("stroke-width")).toBe("8.5");
    const tab = mount(BrandMark, { props: { size: 16 } });
    expect(tab.findAll(".brand-logo-loop")).toHaveLength(1);
    expect(tab.find(".brand-logo-diamond").attributes("stroke-width")).toBe("8");
    expect(tab.find(".brand-logo-diamond").attributes("d")).not.toBe(big.find(".brand-logo-diamond").attributes("d"));
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
    expect(thinking.findAll(".mascot-dot")).toHaveLength(3);
    expect(thinking.find(".mascot-line").exists()).toBe(false);
    expect(thinking.find(".mascot-star").exists()).toBe(false);

    const found = mount(AssistantMascot, { props: { size: 150, mood: "found" } });
    expect(found.findAll(".mascot-star")).toHaveLength(2);
    expect(found.find(".mascot-mouth").exists()).toBe(true);
    expect(found.find(".mascot-line").exists()).toBe(false);
    expect(found.attributes("aria-hidden")).toBe("true");
  });
});
