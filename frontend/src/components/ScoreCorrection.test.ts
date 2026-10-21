import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { UNDO_MS } from "../composables/useUndo";
import ScoreCorrection from "./ScoreCorrection.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));
afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
});

async function mountIt() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  GET.mockResolvedValue({ data: null });
  const wrapper = mount(ScoreCorrection, { props: { offerId: 7 }, global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("Cette note ne me correspond pas (docs/114)", () => {
  it("trop haute, pas mon métier : le bloc proposé, modifiable, ajouté au bout de 6 secondes", async () => {
    vi.useFakeTimers();
    const wrapper = await mountIt();
    POST.mockResolvedValueOnce({
      data: { block: { kind: "redhibitoire", title: "Pas de vente", content: "Pas de vente en magasin.", by_ai: true }, criteria: [] },
    });
    PUT.mockResolvedValueOnce({ data: { direction: "high", reason: "not_my_trade", chunk_id: 3, score_before: 78, score: 32 } });
    await wrapper.find("[data-test=score-correction-open]").trigger("click");
    await wrapper.find("[data-test=score-correction-high]").trigger("click");
    // Les raisons suivent le sens : « Le secteur me plaît » n'est pas proposé pour trop haute.
    expect(wrapper.find("[data-test=score-correction-reason-sector_ok]").exists()).toBe(false);
    await wrapper.find("[data-test=score-correction-reason-not_my_trade]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body).toEqual({ direction: "high", reason: "not_my_trade", note: null });
    expect(wrapper.find("[data-test=score-correction-block]").text()).toContain("Rédhibitoire");
    await wrapper.find("[data-test=score-correction-title]").setValue("Pas de vente en magasin");
    await wrapper.find("[data-test=score-correction-add]").trigger("click");
    expect(wrapper.find("[data-test=score-correction-saved]").text()).toContain("trop haute, ce n'est pas mon métier");
    expect(PUT).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(UNDO_MS);
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body).toEqual({
      direction: "high",
      reason: "not_my_trade",
      note: null,
      block: { kind: "redhibitoire", title: "Pas de vente en magasin", content: "Pas de vente en magasin." },
    });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("lieu, taux ou contrat : un critère en un clic, ou le lien vers les critères", async () => {
    vi.useFakeTimers();
    const wrapper = await mountIt();
    POST.mockResolvedValueOnce({
      data: { block: null, criteria: [{ key: "contract_stage", label: "Écarter les stages", changes: { excluded_types: ["stage"] } }] },
    });
    PUT.mockResolvedValueOnce({ data: { direction: "high", reason: "place_rate_contract", chunk_id: null, score: 78 } });
    await wrapper.find("[data-test=score-correction-open]").trigger("click");
    await wrapper.find("[data-test=score-correction-high]").trigger("click");
    await wrapper.find("[data-test=score-correction-reason-place_rate_contract]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=score-correction-criteria-link]").attributes("href")).toBe("/profil");
    await wrapper.find("[data-test=score-correction-change-contract_stage]").trigger("click");
    await vi.advanceTimersByTimeAsync(UNDO_MS);
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body.criteria).toEqual({ excluded_types: ["stage"] });
  });

  it("« Autre » demande quelques mots avant de proposer", async () => {
    const wrapper = await mountIt();
    await wrapper.find("[data-test=score-correction-open]").trigger("click");
    await wrapper.find("[data-test=score-correction-low]").trigger("click");
    await wrapper.find("[data-test=score-correction-reason-other]").trigger("click");
    expect(POST).not.toHaveBeenCalled();
    POST.mockResolvedValueOnce({ data: { block: { kind: "preference", title: "T", content: "C", by_ai: false }, criteria: [] } });
    await wrapper.find("[data-test=score-correction-note]").setValue("Je connais bien ce métier.");
    await wrapper.find("[data-test=score-correction-other]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body.note).toBe("Je connais bien ce métier.");
  });

  it("une correction déjà faite se lit sur la fiche", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    GET.mockResolvedValue({ data: { direction: "low", reason: "my_trade", chunk_id: 2, score_before: 40, score: 71 } });
    const wrapper = mount(ScoreCorrection, { props: { offerId: 7 }, global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=score-correction-saved]").text()).toBe(
      "Tu as corrigé cette note : trop basse, c'est bien mon métier.",
    );
    expect(wrapper.find("[data-test=score-correction-open]").text()).toBe("Corriger à nouveau");
  });
});
