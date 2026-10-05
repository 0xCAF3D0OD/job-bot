import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter, type Router } from "vue-router";

import { fromQuery, toQuery } from "../composables/useOfferFilters";
import OffersView from "./OffersView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

const offer = (id: number, title: string, extra: Record<string, unknown> = {}) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne, VD",
  rate_min: 80,
  rate_max: 100,
  snippet: "Gérer l'infrastructure.",
  status: "to_review",
  first_seen_at: "2026-10-02T08:00:00Z",
  last_seen_at: "2026-10-02T08:00:00Z",
  seen_count: 1,
  links: [{ source: "jobup", url: `https://www.jobup.ch/fr/emplois/detail/${id}/` }],
  filter_reasons: [],
  ...extra,
});

function page(items: unknown[]) {
  return {
    data: {
      items,
      total: items.length,
      counts: { to_review: 5, filtered_out: 2, all: 7 },
      facets: {
        sources: [
          { value: "indeed", count: 3 },
          { value: "jobup", count: 4 },
        ],
        cantons: [
          { value: "VD", count: 4 },
          { value: "GE", count: 1 },
        ],
      },
    },
  };
}

let router: Router;

async function mountAt(path: string) {
  router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/offres", component: OffersView }],
  });
  await router.push(path);
  const wrapper = mount(OffersView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

function lastQuery(): Record<string, unknown> {
  return (GET.mock.calls.at(-1)?.[1] as { params: { query: Record<string, unknown> } }).params.query;
}

beforeEach(() => GET.mockResolvedValue(page([offer(1, "Ingénieur système")])));
afterEach(() => {
  GET.mockReset();
  vi.useRealTimers();
});

describe("filtres dans l'adresse", () => {
  it("lit et écrit les filtres", () => {
    const filters = fromQuery({ canton: ["vd", "GE"], site: "jobup", taux: "80", externe: "1", statut: "all" });
    expect(filters).toMatchObject({
      view: "all",
      cantons: ["VD", "GE"],
      sources: ["jobup"],
      minRate: 80,
      externalOnly: true,
    });
    expect(toQuery(filters)).toEqual({
      statut: "all",
      canton: ["VD", "GE"],
      site: ["jobup"],
      taux: "80",
      externe: "1",
    });
    expect(fromQuery({ taux: "abc", site: "monster", statut: "?" })).toMatchObject({
      minRate: null,
      sources: [],
      view: "to_review",
    });
  });
});

describe("OffersView", () => {
  it("transmet les filtres de l'adresse à l'API", async () => {
    await mountAt("/offres?canton=VD&taux=80&site=jobup&externe=1&q=linux");
    expect(lastQuery()).toMatchObject({
      view: "to_review",
      cantons: ["VD"],
      min_rate: 80,
      sources: ["jobup"],
      external_only: true,
      q: "linux",
    });
  });

  it("un clic sur un filtre met à jour l'adresse et recharge", async () => {
    const wrapper = await mountAt("/offres");
    expect(wrapper.find("[data-test=view-filtered_out]").text()).toContain("2");
    await wrapper.find("[data-test=canton-VD]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ canton: ["VD"] });
    expect(lastQuery()).toMatchObject({ cantons: ["VD"] });

    await wrapper.find("[data-test=source-indeed]").trigger("change");
    await wrapper.find("[data-test=view-all]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ canton: ["VD"], site: ["indeed"], statut: "all" });
    expect(wrapper.find("[data-test=reset]").text()).toContain("(2)");

    await wrapper.find("[data-test=reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ statut: "all" });
  });

  it("la recherche attend la fin de la frappe", async () => {
    vi.useFakeTimers();
    const wrapper = await mountAt("/offres");
    const calls = GET.mock.calls.length;
    await wrapper.find("[data-test=search]").setValue("dev");
    await wrapper.find("[data-test=search]").setValue("devops");
    expect(GET.mock.calls.length).toBe(calls);
    await vi.advanceTimersByTimeAsync(350);
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ q: "devops" });
    expect(lastQuery()).toMatchObject({ q: "devops" });
  });

  it("détail : candidature, raisons, texte complet, fermeture", async () => {
    GET.mockResolvedValue(
      page([
        offer(7, "Ingénieur VMware", {
          apply_url: "https://www.aplitrak.com/?adid=x",
          apply_kind: "external",
          description: "Notre client recherche un ingénieur.",
          employment_type: "Temporaire",
        }),
        offer(8, "Stage DevOps", { status: "filtered_out", filter_reasons: ["Type : stage (« stage »)"] }),
      ]),
    );
    const wrapper = await mountAt("/offres");
    const cards = wrapper.findAll("[data-test=offer]");
    expect(cards[0]?.text()).toContain("chez l'employeur");
    expect(cards[0]?.text()).toContain("à noter");
    expect(cards[1]?.find(".badge.reason").text()).toBe("Type : stage (« stage »)");

    await cards[0]?.trigger("click");
    const apply = wrapper.find("[data-test=apply]");
    expect(apply.text()).toContain("Postuler chez l'employeur");
    expect(apply.attributes("rel")).toBe("noopener noreferrer");
    expect(wrapper.find("[data-test=description]").text()).toBe("Notre client recherche un ingénieur.");
    expect(wrapper.text()).toContain("Temporaire");

    await wrapper.find("[data-test=close-detail]").trigger("click");
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);

    await cards[1]?.trigger("click");
    expect(wrapper.find("[data-test=reasons]").text()).toContain("Type : stage");
  });
});
