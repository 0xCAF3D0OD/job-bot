import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LayoutCard from "./LayoutCard.vue";

describe("LayoutCard", () => {
  it("la vignette Bandeau dessine le bandeau pêche du document (Kevin, 15.11.2026)", () => {
    const wrapper = mount(LayoutCard);
    const thumb = wrapper.find("[data-test=layout-bandeau] svg");
    expect(thumb.find("rect[fill='#F3B08A']").exists()).toBe(true);
    expect(thumb.find("rect[fill='#1B1F2A']").exists()).toBe(true);
    expect(thumb.find(".thumb-ink").exists()).toBe(false);
  });
});
