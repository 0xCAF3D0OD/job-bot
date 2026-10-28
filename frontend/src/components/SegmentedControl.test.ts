import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SegmentedControl from "./SegmentedControl.vue";

describe("SegmentedControl (règles §4)", () => {
  it("en liens : le segment actif porte aria-current, toute la largeur avec `full`", () => {
    const wrapper = mount(SegmentedControl, {
      props: {
        label: "Profil",
        full: true,
        modelValue: "parcours",
        options: [
          { value: "criteres", label: "Critères", to: "/profil" },
          { value: "parcours", label: "Parcours", to: "/profil?onglet=parcours" },
          { value: "coordonnees", label: "Coordonnées", to: "/profil?onglet=coordonnees" },
        ],
      },
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    expect(wrapper.find("nav").attributes("aria-label")).toBe("Profil");
    expect(wrapper.find("nav").classes()).toContain("segmented-full");
    const links = wrapper.findAllComponents(RouterLinkStub);
    expect(links.map((l) => l.attributes("aria-current"))).toEqual([undefined, "page", undefined]);
    expect(wrapper.findAll(".segmented-label").map((l) => l.text())).toEqual(["Critères", "Parcours", "Coordonnées"]);
  });

  it("en radios : aria-checked, un clic change la valeur", async () => {
    const wrapper = mount(SegmentedControl, {
      props: {
        label: "Période",
        modelValue: "mois",
        "onUpdate:modelValue": (v: string) => wrapper.setProps({ modelValue: v }),
        options: [{ value: "mois", label: "Un mois" }, { value: "tout", label: "Tout" }],
      },
    });
    expect(wrapper.find("[role=radiogroup]").exists()).toBe(true);
    await wrapper.find("[data-test=segment-tout]").trigger("click");
    expect(wrapper.find("[data-test=segment-tout]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=segment-mois]").attributes("aria-checked")).toBe("false");
  });
});
