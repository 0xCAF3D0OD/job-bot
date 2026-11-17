import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AlertsSearchPanel from "./AlertsSearchPanel.vue";

const GET = vi.fn();
const PUT = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const page: any = { mailbox: "moi@exemple.ch", sites: [], searches: [{ id: 1, terms: "DevOps", location: "Lausanne", active: true, cells: [] }] };
const criteria = { locations: ["Lausanne"], min_rate: null, keywords: [] };

async function mountPanel() {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/criteria" ? { data: { criteria } } : { data: { roles: ["DevOps", "SRE"] } }),
  );
  const wrapper = mount(AlertsSearchPanel, { props: { open: true, page }, global: { stubs: { teleport: true } } });
  await flushPromises();
  return wrapper;
}

describe("Le volet « Ta recherche » (Kevin, 17.11)", () => {
  it("postes cochés, lieux, 7 taux en choix unique, l'encadré d'information", async () => {
    const wrapper = await mountPanel();
    const roles = wrapper.findAll("[data-test=search-panel-roles] .filter-choice");
    expect(roles.map((r) => [r.text(), r.attributes("aria-pressed")])).toEqual([
      ["DevOps", "true"],
      ["SRE", "true"],
      ["+ Autre poste", undefined],
    ]);
    expect(wrapper.find("[data-test=search-panel-places]").text()).toContain("Lausanne");
    const rates = wrapper.findAll("[role=radio]");
    expect(rates.map((r) => r.text())).toEqual(["Tous", "Dès 50 %", "Dès 60 %", "Dès 70 %", "Dès 80 %", "Dès 90 %", "100 %"]);
    expect(rates[0]!.attributes("aria-checked")).toBe("true");
    expect(wrapper.find(".alerts-search-info").text()).toBe("Ces critères servent aussi à trier tes offres.");
  });

  it("au-delà de 8 recherches : « Enregistrer » désactivé, le message relié par aria-describedby", async () => {
    const wrapper = await mountPanel();
    for (const place of ["Genève", "Sion", "Fribourg", "Neuchâtel"]) {
      await wrapper.find("[data-test=search-panel-place-input]").setValue(place);
      await wrapper.find("[data-test=search-panel-place-input]").trigger("keydown.enter");
    }
    // 2 postes × 5 lieux = 10 recherches.
    const save = wrapper.find("[data-test=search-panel-save]");
    expect(save.attributes("disabled")).toBeDefined();
    expect(save.attributes("aria-describedby")).toBe("search-panel-limit");
    expect(wrapper.find("#search-panel-limit").text()).toBe("8 recherches au maximum. Retire un poste ou un lieu.");
    // Retirer un poste : 5 recherches, « Enregistrer » revient.
    await wrapper.findAll("[data-test=search-panel-roles] .filter-choice")[1]!.trigger("click");
    expect(wrapper.find("[data-test=search-panel-save]").attributes("disabled")).toBeUndefined();
    expect(wrapper.find("#search-panel-limit").exists()).toBe(false);
  });

  it("« Enregistrer » écrit les critères et rend la page", async () => {
    const wrapper = await mountPanel();
    PUT.mockImplementation((path: string, { body }: { body: unknown }) => Promise.resolve({ data: path === "/api/criteria" ? { criteria: body } : body }));
    POST.mockResolvedValue({ data: page });
    await wrapper.find("[data-test=search-panel-rate-80]").trigger("click");
    await wrapper.find("[data-test=search-panel-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/criteria", { body: { ...criteria, min_rate: 80 } });
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "SRE", location: "Lausanne" } });
    expect(wrapper.emitted("saved")).toHaveLength(1);
  });
});
