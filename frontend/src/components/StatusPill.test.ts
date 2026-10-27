import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import StatusPill from "./StatusPill.vue";

describe("Pastille d'état (1.6.74)", () => {
  it("le ton en classe, le point décoratif, le mot lisible", () => {
    const wrapper = mount(StatusPill, { props: { tone: "todo" }, slots: { default: "Rien reçu depuis la création" } });
    expect(wrapper.classes()).toEqual(expect.arrayContaining(["state-pill", "todo"]));
    expect(wrapper.find(".state-pill-dot").attributes("aria-hidden")).toBe("true");
    expect(wrapper.text()).toBe("Rien reçu depuis la création");
  });

  it("sans point : une étiquette, neutre par défaut", () => {
    const wrapper = mount(StatusPill, { props: { dot: false }, slots: { default: "Spontanée" } });
    expect(wrapper.classes()).toEqual(expect.arrayContaining(["neutral", "tag"]));
    expect(wrapper.find(".state-pill-dot").exists()).toBe(false);
  });
});
