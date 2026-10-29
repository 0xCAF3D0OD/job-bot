import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import StepProgress from "./StepProgress.vue";

describe("StepProgress", () => {
  it("dit « 2 sur 5 » et remplit deux segments sur cinq", () => {
    const wrapper = mount(StepProgress, { props: { current: 2, total: 5 } });
    expect(wrapper.find(".step-progress-text").text()).toBe("2 sur 5");
    expect(wrapper.find(".step-progress-text").attributes("aria-live")).toBe("polite");
    expect(wrapper.findAll(".step-progress-segment")).toHaveLength(5);
    expect(wrapper.findAll(".step-progress-segment.done")).toHaveLength(2);
    expect(wrapper.find(".step-progress-bar").attributes("aria-hidden")).toBe("true");
  });

  it("au-delà de 10, une barre continue ; le numéro reste dans les bornes", () => {
    const wrapper = mount(StepProgress, { props: { current: 30, total: 20 } });
    expect(wrapper.find(".step-progress-text").text()).toBe("20 sur 20");
    expect(wrapper.find(".step-progress-bar").classes()).toContain("continuous");
    expect(wrapper.findAll(".step-progress-segment")).toHaveLength(1);
    expect(wrapper.find(".step-progress-segment").attributes("style")).toContain("width: 100%");
  });
});
