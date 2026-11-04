// L'apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto, retenue sur l'appareil.
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { useTheme } from "../composables/useTheme";
import AppearancePanel from "./AppearancePanel.vue";

afterEach(() => useTheme().setTheme("auto"));

describe("Apparence", () => {
  it("Auto par défaut ; Sombre et Clair posent data-theme et sont retenus ; Auto les enlève", async () => {
    const wrapper = mount(AppearancePanel);
    const checked = () => wrapper.find("[aria-checked=true]").text();
    expect(checked()).toBe("Auto");
    expect(document.documentElement.dataset.theme).toBeUndefined();

    await wrapper.find("[data-test=theme-dark]").trigger("click");
    expect(checked()).toBe("Sombre");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("jobA1-theme")).toBe("dark");

    await wrapper.find("[data-test=theme-light]").trigger("click");
    expect(document.documentElement.dataset.theme).toBe("light");

    await wrapper.find("[data-test=theme-auto]").trigger("click");
    expect(document.documentElement.dataset.theme).toBeUndefined();
    expect(localStorage.getItem("jobA1-theme")).toBe("auto");
  });
});
