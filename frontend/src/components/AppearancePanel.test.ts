// L'apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto, retenue sur l'appareil.
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { useTextSize } from "../composables/useTextSize";
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

describe("Langue et Taille du texte sur ordinateur (ReglagesOrdinateur, MODIFICATIONS_9 §2.10)", () => {
  afterEach(() => useTextSize().setTextSize("browser"));

  it("absentes sans `detailed` (téléphone)", () => {
    const wrapper = mount(AppearancePanel);
    expect(wrapper.find("[data-test=language-row]").exists()).toBe(false);
    expect(wrapper.find("[data-test=text-size-row]").exists()).toBe(false);
  });

  it("deux lignes, la valeur et un chevron ; Langue ouvre un panneau où seul le français est disponible", async () => {
    const wrapper = mount(AppearancePanel, { props: { detailed: true }, attachTo: document.body });
    expect(wrapper.get("[data-test=language-row]").text()).toBe("LangueFrançais");
    expect(wrapper.get("[data-test=text-size-row]").text()).toBe("Taille du texteSelon le navigateur");
    await wrapper.get("[data-test=language-row]").trigger("click");
    const panel = [...document.querySelectorAll("[data-test=choice-panel]")].find((p) => p.querySelector("h3")?.textContent?.includes("Langue de jobA1"))!;
    const radios = [...panel.querySelectorAll<HTMLInputElement>("input[type=radio]")];
    expect(radios.map((r) => [r.value, r.checked, r.disabled])).toEqual([
      ["fr", true, false],
      ["de", false, true],
      ["en", false, true],
    ]);
    expect(panel.textContent).toContain("La langue des lettres se choisit dans Préparer (FR, DE, EN).");
    wrapper.unmount();
  });

  it("« Grande » agrandit le texte de 25 % et reste retenue", async () => {
    const wrapper = mount(AppearancePanel, { props: { detailed: true }, attachTo: document.body });
    await wrapper.get("[data-test=text-size-row]").trigger("click");
    const large = document.querySelector<HTMLInputElement>("[data-test=choice-large] input")!;
    large.checked = true;
    large.dispatchEvent(new Event("change"));
    await wrapper.vm.$nextTick();
    expect(document.documentElement.classList.contains("text-large")).toBe(true);
    expect(localStorage.getItem("jobA1-text-size")).toBe("large");
    expect(wrapper.get("[data-test=text-size-row]").text()).toBe("Taille du texteGrande");
    wrapper.unmount();
  });
});
