// L'apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto, retenue sur l'appareil.
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { useTextSize } from "../composables/useTextSize";
import { useTheme } from "../composables/useTheme";
import AppearancePanel from "./AppearancePanel.vue";

afterEach(() => useTheme().setTheme("auto"));

describe("Apparence", () => {
  it("Auto par défaut ; Sombre et Clair posent data-theme et sont retenus ; Auto les enlève", async () => {
    // LISEZMOI §56 (17.11) : sur ordinateur, « Apparence » et sa valeur ouvrent un menu (Clair, Sombre, Auto).
    const wrapper = mount(AppearancePanel, { attachTo: document.body });
    const value = () => wrapper.get("[data-test=appearance-menu]").text();
    expect(value()).toBe("Auto");
    expect(document.documentElement.dataset.theme).toBeUndefined();
    await wrapper.get("[data-test=appearance-menu]").trigger("click");
    expect(wrapper.findAll("[role=menuitemradio]").map((b) => b.text())).toEqual(["Clair", "Sombre", "Auto"]);

    await wrapper.find("[data-test=theme-dark]").trigger("click");
    expect(value()).toBe("Sombre");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("jobA1-theme")).toBe("dark");

    await wrapper.get("[data-test=appearance-menu]").trigger("click");
    await wrapper.find("[data-test=theme-light]").trigger("click");
    expect(document.documentElement.dataset.theme).toBe("light");

    await wrapper.get("[data-test=appearance-menu]").trigger("click");
    await wrapper.find("[data-test=theme-auto]").trigger("click");
    expect(document.documentElement.dataset.theme).toBeUndefined();
    expect(localStorage.getItem("jobA1-theme")).toBe("auto");
    wrapper.unmount();
  });

  it("téléphone : la ligne ouvre une feuille à boutons radio ; choisir applique et ferme (§56)", async () => {
    const wrapper = mount(AppearancePanel, { props: { phone: true }, attachTo: document.body });
    const row = wrapper.get("[data-test=appearance-row]");
    expect(row.attributes("aria-haspopup")).toBe("dialog");
    expect(row.text()).toBe("ApparenceAuto");
    await row.trigger("click");
    const sheet = document.querySelector("[data-test=choice-sheet]")!;
    const radios = [...sheet.querySelectorAll<HTMLElement>("[role=radio]")];
    expect(radios.map((r) => [r.textContent?.trim(), r.getAttribute("aria-checked")])).toEqual([
      ["Clair", "false"],
      ["Sombre", "false"],
      ["AutoComme le téléphone", "true"],
    ]);
    radios[1]!.click();
    await wrapper.vm.$nextTick();
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(wrapper.get("[data-test=appearance-row]").text()).toBe("ApparenceSombre");
    wrapper.unmount();
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
