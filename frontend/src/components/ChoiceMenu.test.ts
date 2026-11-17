// Le menu de choix sur ordinateur (LISEZMOI §56 du 17.11) : valeur et chevron, menuitemradio, clavier.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ChoiceMenu from "./ChoiceMenu.vue";

const CHOICES = [
  { value: "light", label: "Clair" },
  { value: "dark", label: "Sombre" },
  { value: "auto", label: "Auto" },
];

describe("ChoiceMenu", () => {
  it("le bouton dit le nom et la valeur ; le menu s’ouvre sur le choix actuel ; choisir ferme et rend le focus", async () => {
    const wrapper = mount(ChoiceMenu, { props: { label: "Apparence", choices: CHOICES, modelValue: "auto" }, attachTo: document.body });
    const button = wrapper.get("button[aria-haspopup=menu]");
    expect(button.attributes("aria-label")).toBe("Apparence : Auto");
    expect(button.attributes("aria-expanded")).toBe("false");
    await button.trigger("click");
    expect(button.attributes("aria-expanded")).toBe("true");
    const items = wrapper.findAll("[role=menuitemradio]");
    expect(items.map((i) => i.attributes("aria-checked"))).toEqual(["false", "false", "true"]);
    expect(document.activeElement).toBe(items[2]!.element);
    await wrapper.get("[role=menu]").trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement).toBe(items[0]!.element);
    await items[1]!.trigger("click");
    expect(wrapper.emitted("update:modelValue")).toEqual([["dark"]]);
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    expect(document.activeElement).toBe(button.element);
    wrapper.unmount();
  });

  it("Échap ferme sans choisir", async () => {
    const wrapper = mount(ChoiceMenu, { props: { label: "Apparence", choices: CHOICES, modelValue: "light" }, attachTo: document.body });
    await wrapper.get("button").trigger("click");
    await wrapper.get("[role=menu]").trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    wrapper.unmount();
  });
});
