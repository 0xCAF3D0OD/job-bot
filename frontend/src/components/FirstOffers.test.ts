import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import FirstOffers from "./FirstOffers.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
beforeEach(() => localStorage.clear());
afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
});

const state = (extra: Record<string, unknown>) => ({ status: "none", at: null, found: 0, new: 0, queries: [], ...extra });

describe("Les premières offres (docs/104, 0.80.0)", () => {
  it("page Offres : la recherche en cours, puis le résultat et l'offre rechargée", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValueOnce({ data: state({ status: "queued" }) });
    const now = new Date().toISOString();
    GET.mockResolvedValueOnce({ data: state({ status: "done", at: now, found: 18, new: 18, queries: ["Menuisier · Sion"] }) });
    const wrapper = mount(FirstOffers, { props: { where: "offers" } });
    await flushPromises();
    expect(wrapper.find("[data-test=first-offers-line]").text()).toContain("Je cherche tes premières offres sur jobup");
    await vi.advanceTimersByTimeAsync(8000);
    await flushPromises();
    expect(wrapper.emitted("arrived")).toHaveLength(1);
    expect(wrapper.find("[data-test=first-offers-line]").text()).toContain("18 premières offres trouvées sur jobup (Menuisier · Sion)");
    await wrapper.find("[data-test=first-offers-dismiss]").trigger("click");
    expect(wrapper.find("[data-test=first-offers-line]").exists()).toBe(false);
  });

  it("page Offres : rien après trois jours, ni sans offre nouvelle", async () => {
    const old = new Date(Date.now() - 4 * 86_400_000).toISOString();
    GET.mockResolvedValueOnce({ data: state({ status: "done", at: old, new: 5 }) });
    const wrapper = mount(FirstOffers, { props: { where: "offers" } });
    await flushPromises();
    expect(wrapper.find("[data-test=first-offers-line]").exists()).toBe(false);
  });

  it("page Alertes : relancer la recherche, une fois par heure", async () => {
    GET.mockResolvedValueOnce({ data: state({ status: "done", at: new Date().toISOString(), found: 10, new: 3, queries: ["Menuisier · Sion"] }) });
    POST.mockResolvedValueOnce({ data: { ...state({ status: "done", found: 10, new: 3, queries: ["Menuisier · Sion"] }), result: "too_soon" } });
    const wrapper = mount(FirstOffers, { props: { where: "alerts" } });
    await flushPromises();
    expect(wrapper.find("[data-test=first-offers]").text()).toContain("10 offres trouvées, dont 3 nouvelles");
    await wrapper.find("[data-test=first-offers-start]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/first-offers");
    expect(wrapper.find("[data-test=first-offers-message]").text()).toContain("moins d'une heure");
  });

  it("page Alertes : sans métier, il le dit", async () => {
    GET.mockResolvedValueOnce({ data: state({ status: "no_trade" }) });
    const wrapper = mount(FirstOffers, { props: { where: "alerts" } });
    await flushPromises();
    expect(wrapper.text()).toContain("Indique d'abord ton métier");
  });
});
