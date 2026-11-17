// « Première candidature notée » (section 44 du 17.11, planches AccueilPremiereCandidature et
// AujourdhuiOrdinateurPremiereCandidature).
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import FirstApplicationCard from "./FirstApplicationCard.vue";

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:p(.*)*", component: { template: "<div />" } }] });
const props = { company: "Logitech", sentAt: "2026-11-12", applicationId: 7, count: 6, target: 10 };
const find = (sel: string) => document.body.querySelector(sel);
const all = (sel: string) => document.body.querySelectorAll(sel).length;

describe("FirstApplicationCard", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    vi.useRealTimers();
  });

  it("nomme la candidature, montre le mois ORP et ouvre la candidature, comme la planche", async () => {
    const wrapper = mount(FirstApplicationCard, { props, global: { plugins: [router] }, attachTo: document.body });
    await router.isReady();
    const card = find("[data-test=first-steps-done]");
    expect(card?.getAttribute("role")).toBe("status");
    expect(find(".fa-title")?.textContent).toBe("Première candidature notée");
    expect(find("[data-test=first-application-line]")?.textContent).toBe("Logitech · 12 nov.");
    // 10 segments : 5 d'avant en bleu, la nouvelle en pêche, 4 à faire.
    expect([all("[data-test=first-application-seg-done]"), all("[data-test=first-application-seg-new]"), all("[data-test=first-application-seg-todo]")]).toEqual([5, 1, 4]);
    expect(find(".fa-count")?.textContent).toBe("Compte pour ton mois ORP : 6 sur 10");
    expect(find("[data-test=first-application-see]")?.getAttribute("href")).toBe("/candidatures/suivi?candidature=7");
    // Sans voile ni focus pris : l'app reste utilisable.
    expect(document.activeElement).toBe(document.body);
    expect(find(".success-overlay")).toBeNull();
    wrapper.unmount();
  });

  it("reste ouverte : toujours visible après 10 s, sans minuteur (Kevin, 17.11)", () => {
    vi.useFakeTimers();
    const wrapper = mount(FirstApplicationCard, { props, global: { plugins: [router] }, attachTo: document.body });
    expect(vi.getTimerCount()).toBe(0);
    vi.advanceTimersByTime(10_000);
    expect(find("[data-test=first-steps-done]")).not.toBeNull();
    expect(find(".fa-card.leaving")).toBeNull();
    expect(wrapper.emitted("close")).toBeUndefined();
    wrapper.unmount();
  });

  it("se ferme avec « Fermer » ou Échap", async () => {
    vi.useFakeTimers();
    const wrapper = mount(FirstApplicationCard, { props, global: { plugins: [router] }, attachTo: document.body });
    (find("button[aria-label=Fermer]") as HTMLButtonElement).click();
    vi.advanceTimersByTime(250);
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();

    const byKey = mount(FirstApplicationCard, { props, global: { plugins: [router] }, attachTo: document.body });
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    vi.advanceTimersByTime(250);
    expect(byKey.emitted("close")).toHaveLength(1);
    byKey.unmount();

  });

  it("sans objectif réglé : ni barre ni « sur N »", () => {
    const wrapper = mount(FirstApplicationCard, { props: { ...props, target: null, count: 1 }, global: { plugins: [router] }, attachTo: document.body });
    expect(find(".fa-bar")).toBeNull();
    expect(find(".fa-count")?.textContent).toBe("Compte pour ton mois ORP : 1");
    wrapper.unmount();
  });
});
