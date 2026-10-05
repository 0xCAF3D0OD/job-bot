import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import OffersView from "./OffersView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

afterEach(() => GET.mockReset());

const offer = (id: number, title: string, extra: Record<string, unknown> = {}) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne",
  rate_min: 80,
  rate_max: 100,
  snippet: "Gérer l'infrastructure.",
  status: "new",
  first_seen_at: "2026-10-02T08:00:00Z",
  last_seen_at: "2026-10-02T08:00:00Z",
  seen_count: 1,
  links: [{ source: "jobup", url: `https://www.jobup.ch/fr/emplois/detail/${id}/` }],
  ...extra,
});

describe("OffersView", () => {
  it("affiche le détail de l'offre choisie à côté de la liste", async () => {
    GET.mockResolvedValue({
      data: {
        items: [
          offer(1, "Ingénieur système"),
          offer(2, "DevOps", {
            seen_count: 2,
            links: [
              { source: "jobup", url: "https://www.jobup.ch/x/" },
              { source: "indeed", url: "https://ch.indeed.com/viewjob?jk=k" },
            ],
          }),
        ],
        total: 2,
        counts: { to_review: 2, filtered_out: 0, all: 2 },
      },
    });
    const wrapper = mount(OffersView);
    await flushPromises();
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);
    expect(wrapper.text()).toContain("Choisis une offre");

    const cards = wrapper.findAll("[data-test=offer]");
    expect(cards[1]?.text()).toContain("vue 2 fois");
    expect(cards[1]?.text()).toContain("jobup, Indeed");
    await cards[1]?.trigger("click");

    const detail = wrapper.find("[data-test=offer-detail]");
    expect(detail.find("h2").text()).toBe("DevOps");
    expect(detail.text()).toContain("80–100 %");
    const links = detail.findAll(".actions a");
    expect(links.map((a) => a.text().trim())).toEqual(["Voir sur jobup", "Voir sur Indeed"]);
    expect(links.every((a) => a.attributes("rel") === "noopener noreferrer")).toBe(true);
  });
});

it("le tri Populaires est transmis à l'API", async () => {
  GET.mockResolvedValue({
    data: { items: [offer(1, "A")], total: 1, counts: { to_review: 1, filtered_out: 0, all: 1 } },
  });
  const wrapper = mount(OffersView);
  await flushPromises();
  await wrapper.find("[data-test=sort-popular]").trigger("click");
  await flushPromises();
  expect(GET.mock.calls.at(-1)?.[1]).toMatchObject({ params: { query: { sort: "popular" } } });
});

it("onglets par statut et raisons d'exclusion", async () => {
  GET.mockResolvedValue({
    data: {
      items: [offer(3, "Stage DevOps", { status: "filtered_out", filter_reasons: ["Type : stage (« stage »)"] })],
      total: 1,
      counts: { to_review: 5, filtered_out: 1, all: 6 },
    },
  });
  const wrapper = mount(OffersView);
  await flushPromises();
  expect(GET.mock.calls[0]?.[1]).toMatchObject({ params: { query: { view: "to_review" } } });
  expect(wrapper.find("[data-test=view-filtered_out]").text()).toContain("1");

  await wrapper.find("[data-test=view-filtered_out]").trigger("click");
  await flushPromises();
  expect(GET.mock.calls.at(-1)?.[1]).toMatchObject({ params: { query: { view: "filtered_out" } } });
  const card = wrapper.find("[data-test=offer]");
  expect(card.find(".badge.reason").text()).toBe("Type : stage (« stage »)");
  await card.trigger("click");
  expect(wrapper.find("[data-test=reasons]").text()).toContain("Type : stage");
});

it("bouton de candidature chez l'employeur et texte complet", async () => {
  GET.mockResolvedValue({
    data: {
      items: [
        offer(7, "Ingénieur VMware", {
          apply_url: "https://www.aplitrak.com/?adid=x",
          apply_kind: "external",
          description: "Notre client recherche un ingénieur.",
          employment_type: "Temporaire",
          enrich_status: "ok",
        }),
      ],
      total: 1,
      counts: { to_review: 1, filtered_out: 0, all: 1 },
    },
  });
  const wrapper = mount(OffersView);
  await flushPromises();
  await wrapper.find("[data-test=offer]").trigger("click");
  const apply = wrapper.find("[data-test=apply]");
  expect(apply.text()).toContain("Postuler chez l'employeur");
  expect(apply.attributes("href")).toBe("https://www.aplitrak.com/?adid=x");
  expect(apply.attributes("rel")).toBe("noopener noreferrer");
  expect(wrapper.find("[data-test=description]").text()).toBe("Notre client recherche un ingénieur.");
  expect(wrapper.text()).toContain("Temporaire");
});
