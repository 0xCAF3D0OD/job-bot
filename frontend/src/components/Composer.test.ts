import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import Composer from "./Composer.vue";
import { closeAllLayers } from "../composables/useDismissLayer";

const ITEMS = [
  { id: "cv", label: "Joindre mon CV", hint: "CV_Kevin.pdf", icon: "file" as const },
  { id: "offer", label: "Joindre une offre de ma liste", icon: "briefcase" as const },
];

afterEach(() => {
  closeAllLayers();
  document.body.innerHTML = "";
});

describe("Composer (docs/143, D25)", () => {
  it("Entrée envoie, Maj + Entrée passe à la ligne ; Envoyer porte son nom accessible", async () => {
    const wrapper = mount(Composer, { props: { modelValue: "Bonjour", placeholder: "Demander à l’Assistant", sendLabel: "Envoyer le message" } });
    const input = wrapper.get("[data-test=composer-input]");
    expect(input.attributes("aria-label")).toBe("Demander à l’Assistant");
    await input.trigger("keydown", { key: "Enter", shiftKey: true });
    expect(wrapper.emitted("send")).toBeUndefined();
    await input.trigger("keydown", { key: "Enter" });
    expect(wrapper.emitted("send")).toEqual([["Bonjour"]]);
    expect(wrapper.get("[data-test=composer-send]").attributes("aria-label")).toBe("Envoyer le message");
  });

  it("Envoyer est désactivé si le champ est vide et sans pièce jointe, ou sous minChars", async () => {
    const wrapper = mount(Composer, { props: { modelValue: "  ", placeholder: "Message" } });
    expect(wrapper.get("[data-test=composer-send]").attributes("disabled")).toBeDefined();
    await wrapper.setProps({ attachments: [{ id: "cv", label: "CV.pdf" }] });
    expect(wrapper.get("[data-test=composer-send]").attributes("disabled")).toBeUndefined();
    await wrapper.get("[data-test=composer-remove-cv]").trigger("click");
    expect(wrapper.emitted("remove")).toEqual([["cv"]]);
    await wrapper.setProps({ attachments: [], modelValue: "court", minChars: 200, rows: 5, counterHint: "la flèche enregistre et refait la note" });
    expect(wrapper.get("[data-test=composer-send]").attributes("disabled")).toBeDefined();
    expect(wrapper.get("[data-test=composer-counter]").text()).toBe("5 caractères, 200 au moins · la flèche enregistre et refait la note");
  });

  it("le menu + s’ouvre, se parcourt aux flèches et joint l’élément choisi", async () => {
    const wrapper = mount(Composer, { attachTo: document.body, props: { modelValue: "", placeholder: "Message", plusItems: ITEMS } });
    const plus = wrapper.get("[data-test=composer-plus]");
    expect(plus.attributes("aria-label")).toBe("Joindre un fichier");
    await plus.trigger("click");
    expect(plus.attributes("aria-expanded")).toBe("true");
    expect(wrapper.get("[data-test=composer-menu]").attributes("role")).toBe("menu");
    await wrapper.get("[data-test=composer-item-offer]").trigger("click");
    expect(wrapper.emitted("attach")).toEqual([["offer"]]);
    expect(wrapper.find("[data-test=composer-menu]").exists()).toBe(false);
  });

  it("le micro reste caché quand le navigateur ne sait pas dicter", () => {
    const wrapper = mount(Composer, { props: { modelValue: "", placeholder: "Message", mic: true } });
    expect(wrapper.find("[data-test=composer-mic]").exists()).toBe(false);
  });

  it("le premier appui sur le micro demande l’accord (O-4) ; « Annuler » ne dicte rien", async () => {
    const started: string[] = [];
    class FakeRecognition {
      lang = "";
      onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null = null;
      onend: (() => void) | null = null;
      start(): void {
        started.push(this.lang);
        this.onresult?.({ results: [[{ transcript: "bonjour" }]] });
      }
    }
    vi.stubGlobal("webkitSpeechRecognition", FakeRecognition);
    localStorage.removeItem("jobA1.dictee");
    const wrapper = mount(Composer, { props: { modelValue: "", placeholder: "Message", mic: true, stacked: true } });
    await wrapper.get("[data-test=composer-mic]").trigger("click");
    expect(wrapper.get("[data-test=composer-mic-consent]").text()).toContain("Google");
    await wrapper.get("[data-test=inline-confirm-no]").trigger("click");
    expect(started).toEqual([]);
    await wrapper.get("[data-test=composer-mic]").trigger("click");
    await wrapper.get("[data-test=inline-confirm-yes]").trigger("click");
    expect(started).toEqual(["fr-CH"]);
    expect(wrapper.emitted("update:modelValue")).toEqual([["bonjour"]]);
    expect(localStorage.getItem("jobA1.dictee")).toBe("oui");
    // Accord donné : le micro dicte tout de suite.
    await wrapper.get("[data-test=composer-mic]").trigger("click");
    expect(started).toHaveLength(2);
    expect(wrapper.find("[data-test=composer-mic-consent]").exists()).toBe(false);
    vi.unstubAllGlobals();
    localStorage.removeItem("jobA1.dictee");
  });
});

describe("Composer en boîte (prompt du 10 novembre, PR 19 ; maquettes Assistant et AssistantOrdinateur)", () => {
  it("le texte en haut, + à gauche et Envoyer à droite en dessous, même sur une ligne", () => {
    const wrapper = mount(Composer, { props: { modelValue: "", placeholder: "Demander à l’Assistant", stacked: true, plusItems: ITEMS } });
    expect(wrapper.classes()).toContain("composer-stacked");
    expect(wrapper.get("textarea").element.tagName).toBe("TEXTAREA");
    const bar = wrapper.get(".composer-stacked-bar");
    expect(bar.find("[data-test=composer-plus]").exists()).toBe(true);
    expect(bar.element.lastElementChild?.getAttribute("data-test")).toBe("composer-send");
    expect(wrapper.findAll("[data-test=composer-send]")).toHaveLength(1);
  });

  it("Envoyer reste visible : gris et aria-disabled à vide, actif avec du texte", async () => {
    const wrapper = mount(Composer, { props: { modelValue: "", placeholder: "Message", stacked: true } });
    const send = wrapper.get("[data-test=composer-send]");
    expect(send.attributes("aria-disabled")).toBe("true");
    expect(send.attributes("disabled")).toBeUndefined();
    await send.trigger("click");
    expect(wrapper.emitted("send")).toBeUndefined();
    await wrapper.setProps({ modelValue: "Prépare ma lettre" });
    expect(wrapper.get("[data-test=composer-send]").attributes("aria-disabled")).toBeUndefined();
    await wrapper.get("[data-test=composer-input]").trigger("keydown", { key: "Enter" });
    expect(wrapper.emitted("send")).toEqual([["Prépare ma lettre"]]);
  });
});
