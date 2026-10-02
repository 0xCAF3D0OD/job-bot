import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import JournalView from "./JournalView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...args: unknown[]) => GET(...args),
    POST: (...args: unknown[]) => POST(...args),
  },
}));

afterEach(() => {
  GET.mockReset();
  POST.mockReset();
});

const search = {
  id: 7,
  source: "jobup",
  received_at: "2026-10-02T08:00:00Z",
  subject: "3 nouvelles offres",
  alert_label: "Ingénieur système Lausanne",
  parse_status: "parsed",
  parser_version: "1",
  error: null,
  results_count: 1,
  new_offers_count: 1,
  collected_at: "2026-10-02T08:05:00Z",
};

const detail = {
  ...search,
  offers: [
    {
      id: 1,
      title: "Ingénieur système",
      company: "Acme SA",
      location: "Lausanne",
      rate_min: 80,
      rate_max: 100,
      snippet: null,
      status: "new",
      first_seen_at: "2026-10-02T08:00:00Z",
      last_seen_at: "2026-10-02T08:00:00Z",
      seen_count: 1,
      links: [{ source: "jobup", url: "https://www.jobup.ch/offre/1" }],
      is_first: true,
    },
  ],
};

function mockApi(): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data: path === "/api/searches" ? { items: [search], total: 1 } : detail,
    }),
  );
}

describe("JournalView", () => {
  it("liste les alertes et affiche les offres d'une alerte au clic", async () => {
    mockApi();
    const wrapper = mount(JournalView);
    await flushPromises();
    const rows = wrapper.findAll("[data-test=search]");
    expect(rows).toHaveLength(1);
    expect(rows[0]?.text()).toContain("Ingénieur système Lausanne");
    expect(rows[0]?.text()).toContain("analysé");

    await rows[0]?.trigger("click");
    await flushPromises();
    const offer = wrapper.find("[data-test=detail-offer]");
    expect(offer.text()).toContain("nouvelle");
    expect(offer.text()).toContain("80–100 %");
    const link = offer.find("a");
    expect(link.attributes("rel")).toBe("noopener noreferrer");
    expect(link.attributes("href")).toBe("https://www.jobup.ch/offre/1");
  });

  it("transmet les filtres à l'API", async () => {
    mockApi();
    const wrapper = mount(JournalView);
    await flushPromises();
    await wrapper.find("[data-test=filter-source]").setValue("indeed");
    await flushPromises();
    const lastCall = GET.mock.calls.at(-1);
    expect(lastCall?.[1]).toMatchObject({ params: { query: { source: "indeed", offset: 0 } } });
  });

  it.each([
    [{ status: 202 }, { result: "queued" }, "Collecte lancée"],
    [{ status: 202 }, { result: "already_queued" }, "attend déjà"],
    [{ status: 409 }, undefined, "non configurée"],
  ])("bouton Collecter maintenant (%o, %o)", async (response, data, message) => {
    mockApi();
    POST.mockResolvedValue({ response, data });
    const wrapper = mount(JournalView);
    await flushPromises();
    await wrapper.find("[data-test=collect]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toContain(message);
  });
});
