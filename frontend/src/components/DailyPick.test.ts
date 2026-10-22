// Les offres du jour, une à la fois (docs/124 §D).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import DailyPick from "./DailyPick.vue";

const PATCH = vi.fn();
vi.mock("../api/client", () => ({ api: { PATCH: (...a: unknown[]) => PATCH(...a) } }));
afterEach(() => vi.resetAllMocks());

const offers = [
  { id: 1, title: "DevOps", company: "Acme SA", location: "Lausanne", score: 82, why: "Ta plateforme colle.", keywords_asks: [{ text: "Go", covered: false }], links: [] },
  { id: 2, title: "SRE", company: "Beta SA", location: "Genève", score: 64, keywords_asks: [], links: [] },
];

function mountPick() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  return mount(DailyPick, { props: { offers: offers as never }, global: { plugins: [router] } });
}

describe("DailyPick", () => {
  it("une offre à la fois : sa note, pourquoi, ce qui manque, « 1 sur 2 »", () => {
    const wrapper = mountPick();
    const card = wrapper.find("[data-test=pick-card]");
    expect(card.text()).toContain("DevOps");
    expect(card.text()).toContain("Ta plateforme colle.");
    // La phrase dit déjà ce qui manque : pas de « Il te manque » en plus.
    expect(card.text()).not.toContain("Il te manque");
    expect(card.find("[data-test=pick-count]").text()).toBe("1 sur 2");
  });

  it("Garder puis Écarter : le statut part après coup, « Annuler » remet l'offre", async () => {
    PATCH.mockResolvedValue({ response: { ok: true } });
    const wrapper = mountPick();
    await wrapper.find("[data-test=pick-keep]").trigger("click");
    await flushPromises();
    expect(PATCH).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("SRE");
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
    expect(done.text()).toContain("Tri du jour terminé.");
    expect(done.text()).toContain("1 gardée, 1 écartée.");
    expect(wrapper.emitted("changed")).toBeTruthy();
    await done.find("[data-test=pick-preparing]").trigger("click");
    expect(wrapper.emitted("showPreparing")).toBeTruthy();
  });

  it("au doigt, balayer à gauche écarte ; la souris ne balaie pas", async () => {
    const wrapper = mountPick();
    const el = wrapper.find("[data-test=pick-card]").element;
    const fire = async (type: string, pointerType: string, clientX = 0) => {
      const event = new Event(type, { bubbles: true });
      Object.assign(event, { pointerType, clientX });
      el.dispatchEvent(event);
      await flushPromises();
    };
    await fire("pointerdown", "mouse", 200);
    await fire("pointermove", "mouse", 50);
    await fire("pointerup", "mouse");
    expect(wrapper.find("[data-test=pick-count]").text()).toBe("1 sur 2");
    await fire("pointerdown", "touch", 200);
    await fire("pointermove", "touch", 50);
    await fire("pointerup", "touch");
    await flushPromises();
    expect(wrapper.find("[data-test=pick-card]").text()).toContain("SRE");
    await useUndo().undo();
  });
});
