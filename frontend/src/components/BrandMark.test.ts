import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AssistantMascot from "./AssistantMascot.vue";
import BrandMark from "./BrandMark.vue";

describe("Le logo et la mascotte (docs/97)", () => {
  it("le logo (docs/102) : le visage du 1, penché ; deux traits, un œil, la bille", () => {
    const bar = mount(BrandMark, { props: { size: 28 } });
    expect(bar.attributes("aria-hidden")).toBe("true");
    expect(bar.attributes("viewBox")).toBe("8 8 86 86");
    expect(bar.attributes("width")).toBe("28");
    expect(bar.find("g").attributes("transform")).toBe("rotate(-6 50 50)");
    expect(bar.findAll(".brand-logo-line")).toHaveLength(2);
    expect(bar.findAll(".brand-logo-eye")).toHaveLength(1);
    expect(bar.findAll(".brand-logo-spark")).toHaveLength(1);
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
