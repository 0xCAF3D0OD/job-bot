// Les offres du jour, une à la fois (planche « Tri et panneau de commande »).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import DailyPick from "./DailyPick.vue";

const PATCH = vi.fn();
vi.mock("../api/client", () => ({ api: { PATCH: (...a: unknown[]) => PATCH(...a) } }));
afterEach(() => vi.resetAllMocks());

const offers = [
  { id: 1, title: "DevOps", company: "Acme SA", location: "Lausanne", score: 82, why: "Ta plateforme colle.", keywords_asks: [{ text: "Go", covered: false }], rate_min: 80, rate_max: 100, employment_type: "CDI", remote: "hybrid", remote_days: 2, links: [{ url: "https://www.jobup.ch/fr/emplois/detail/1/", source: "jobup" }] },
  { id: 2, title: "SRE", company: "Beta SA", location: "Genève", score: 64, keywords_asks: [], links: [] },
];

function mountPick() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  return mount(DailyPick, { props: { offers: offers as never }, global: { plugins: [router] } });
}

describe("DailyPick", () => {
  it("une offre à la fois : la note et pourquoi, les étiquettes, l'annonce, sa place", () => {
    const wrapper = mountPick();
    const card = wrapper.find("[data-test=pick-card]");
    expect(card.text()).toContain("DevOps");
    expect(card.text()).toContain("Acme SA · Lausanne");
    expect(card.text()).toContain("Ta plateforme colle.");
    // La phrase dit déjà ce qui manque : pas de « Il te manque » en plus.
    expect(card.text()).not.toContain("Il te manque");
    expect(card.findAll("[data-test=pick-tags] li").map((li) => li.text())).toEqual(["80 à 100 %", "CDI", "Télétravail 2 jours"]);
    const ad = card.find("[data-test=pick-ad]");
    expect(ad.attributes("target")).toBe("_blank");
    expect(ad.text()).toContain("(nouvel onglet)");
    // La place dans la pile, pour la progression de l'écran.
    const vm = wrapper.vm as unknown as { position: number; total: number };
    expect([vm.position, vm.total]).toEqual([1, 2]);
    // Les boutons portent leurs raccourcis.
    expect(wrapper.find("[data-test=pick-dismiss]").attributes("aria-keyshortcuts")).toBe("ArrowLeft");
    expect(wrapper.find("[data-test=pick-keep]").attributes("aria-keyshortcuts")).toBe("ArrowRight");
  });

  it("Garder puis Écarter : le statut part après coup, « Annuler » remet l'offre", async () => {
    PATCH.mockResolvedValue({ response: { ok: true } });
    const wrapper = mountPick();
    await wrapper.find("[data-test=pick-keep]").trigger("click");
    await flushPromises();
    expect(PATCH).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("SRE");
    // « Annuler » entre la carte et les boutons.
    expect(wrapper.find("[data-test=undo-inline]").text()).toContain("Gardée : DevOps.");
    // « Annuler » : la première revient, rien n'est parti.
    await useUndo().undo();
    await flushPromises();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("DevOps");
    await wrapper.find("[data-test=pick-keep]").trigger("click");
    await wrapper.find("[data-test=pick-dismiss]").trigger("click");
    await useUndo().flush();
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/status", expect.objectContaining({ params: { path: { offer_id: 1 } }, body: { status: "preparing" } }));
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/status", expect.objectContaining({ params: { path: { offer_id: 2 } }, body: { status: "ignored" } }));
    const done = wrapper.find("[data-test=pick-done]");
    expect(done.text()).toContain("Tri du jour terminé");
    expect(done.text()).toContain("1 gardée, 1 écartée.");
    expect(done.find("[data-test=pick-preparing]").text()).toBe("Préparer l'offre gardée");
    expect(wrapper.emitted("changed")).toBeTruthy();
    await done.find("[data-test=pick-preparing]").trigger("click");
    expect(wrapper.emitted("showPreparing")).toBeTruthy();
  });

  it("sur téléphone : la note, pourquoi et l'annonce passent dans le panneau, pas de raccourcis", () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px"), addEventListener() {}, removeEventListener() {} }));
    const wrapper = mountPick();
    const card = wrapper.find("[data-test=pick-card]");
    expect(card.text()).not.toContain("Ta plateforme colle.");
    expect(card.find("[data-test=pick-tags]").exists()).toBe(true);
    const bar = wrapper.find("[data-test=action-bar]");
    expect(bar.find("[data-test=pick-score]").text()).toContain("Ta plateforme colle.");
    expect(bar.find("[data-test=pick-ad]").exists()).toBe(true);
    expect(wrapper.find("[data-test=key-hints]").exists()).toBe(false);
    vi.unstubAllGlobals();
    wrapper.unmount();
  });

  it("← écarte et → garde, sauf dans un champ ; pas de balayage", async () => {
    const wrapper = mountPick();
    const input = document.createElement("input");
    document.body.append(input);
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    await flushPromises();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("DevOps");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
    await flushPromises();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("SRE");
    expect(wrapper.find("[data-test=pick-card]").attributes("style")).toBeUndefined();
    input.remove();
    await useUndo().undo();
    wrapper.unmount();
  });
});
