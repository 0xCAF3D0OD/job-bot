import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FaceState from "./FaceState.vue";

describe("État de jobA1 avec illustration (1.6.73, règle §4)", () => {
  it("l'illustration remplace le visage, décorative", () => {
    const wrapper = mount(FaceState, { props: { title: "Aucun rendez-vous ORP prévu", illustration: "rendez-vous-vide" } });
    const illu = wrapper.find("[data-illustration=rendez-vous-vide]");
    expect(illu.exists()).toBe(true);
    expect(illu.classes()).toContain("spot");
    expect(illu.attributes("aria-hidden")).toBe("true");
    expect(illu.find("img").attributes("alt")).toBe("");
    expect(wrapper.find("svg").exists()).toBe(false);
  });

  it("sans illustration : le visage, comme avant", () => {
    const wrapper = mount(FaceState, { props: { title: "Pas encore d'offre" } });
    expect(wrapper.find("[data-illustration]").exists()).toBe(false);
    expect(wrapper.find("svg").exists()).toBe(true);
  });
});
