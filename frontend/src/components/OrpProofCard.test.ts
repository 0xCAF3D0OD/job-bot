// « Justificatifs déjà remis à l'ORP » (récapitulatif du 11 novembre, PR 29 ; maquettes Orp et BilanOrdinateur).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import OrpProofCard from "./OrpProofCard.vue";

const GET = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), DELETE: (...a: unknown[]) => DELETE(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const printSheet = vi.fn();
vi.mock("../composables/usePrint", () => ({ printSheet: (...a: unknown[]) => printSheet(...a) }));

const october = {
  month: "2026-10",
  state: "a_remettre",
  due_date: "2026-11-05",
  count: 11,
  target: 13,
  rows: [],
  holder: { name: "Kevin", address: null },
  searches: [],
  changed_after_submit: false,
  submitted_at: null,
};
let month: Record<string, unknown> = october;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-10T10:00:00"));
  month = october;
  GET.mockImplementation(() => Promise.resolve({ data: month }));
  PUT.mockImplementation(() => {
    month = { ...october, state: "remis", submitted_at: "2026-11-10T09:00:00Z" };
    return Promise.resolve({});
  });
  DELETE.mockImplementation(() => {
    month = october;
    return Promise.resolve({});
  });
  POST.mockResolvedValue({});
});
afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

async function mountCard() {
  const wrapper = mount(OrpProofCard, { global: { stubs: { RouterLink: true } } });
  await flushPromises();
  return wrapper;
}

describe("OrpProofCard", () => {
  it("demande le mois précédent et dit ce qui reste à remettre, échéance passée", async () => {
    const wrapper = await mountCard();
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-10" } } });
    expect(wrapper.get("[data-test=orp-proof]").attributes("role")).toBe("status");
    expect(wrapper.get("[data-test=orp-proof-title]").text()).toBe("Justificatifs d’octobre à remettre");
    expect(wrapper.get("[data-test=orp-proof-line]").text()).toBe("11 recherches · échéance passée le 5 novembre");
    expect(wrapper.get("[data-test=orp-proof-export]").text()).toBe("Exporter le PDF");
    expect(wrapper.get("[data-test=orp-proof-mark]").text()).toBe("Déjà remis");
  });

  it("avant l’échéance : « échéance le 5 novembre »", async () => {
    vi.setSystemTime(new Date("2026-11-03T10:00:00"));
    const wrapper = await mountCard();
    expect(wrapper.get("[data-test=orp-proof-line]").text()).toBe("11 recherches · échéance le 5 novembre");
  });

  it("« Déjà remis » enregistre la remise ; la carte donne la date et « Annuler » revient en arrière", async () => {
    const wrapper = await mountCard();
    await wrapper.get("[data-test=orp-proof-mark]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp/{month}/submission", { params: { path: { month: "2026-10" } } });
    expect(wrapper.get("[data-test=orp-proof-title]").text()).toBe("Octobre remis à l’ORP");
    expect(wrapper.get("[data-test=orp-proof-line]").text()).toBe("Le 10 novembre · 11 recherches");
    expect(wrapper.find("[data-test=orp-proof-mark]").exists()).toBe(false);
    expect(wrapper.emitted("changed")).toHaveLength(1);
    await wrapper.get("[data-test=orp-proof-undo]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/orp/{month}/submission", { params: { path: { month: "2026-10" } } });
    expect(wrapper.get("[data-test=orp-proof-title]").text()).toBe("Justificatifs d’octobre à remettre");
    expect(wrapper.emitted("changed")).toHaveLength(2);
  });

  it("« Exporter le PDF » imprime la feuille du mois précédent", async () => {
    const wrapper = await mountCard();
    await wrapper.get("[data-test=orp-proof-export]").trigger("click");
    await flushPromises();
    expect(printSheet).toHaveBeenCalledTimes(1);
    expect(printSheet.mock.calls[0]![1]).toMatchObject({ title: "Justificatifs ORP - 2026-10" });
    expect(POST).toHaveBeenCalledWith("/api/orp/{month}/exported", { params: { path: { month: "2026-10" } } });
  });

  it("l’enregistrement échoue : rien ne change et la carte le dit", async () => {
    PUT.mockResolvedValueOnce({ error: { detail: "non" } });
    const wrapper = await mountCard();
    await wrapper.get("[data-test=orp-proof-mark]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[role=alert]").text()).toBe("Rien n’a été enregistré. Réessaie.");
    expect(wrapper.get("[data-test=orp-proof-title]").text()).toBe("Justificatifs d’octobre à remettre");
  });

  it("aucune recherche le mois précédent : pas de carte", async () => {
    month = { ...october, count: 0 };
    const wrapper = await mountCard();
    expect(wrapper.find("[data-test=orp-proof]").exists()).toBe(false);
  });
});
