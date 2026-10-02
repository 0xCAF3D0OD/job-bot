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
      },
    });
    const wrapper = mount(OffersView);
    await flushPromises();
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);
    expect(wrapper.text()).toContain("Choisis une offre");

    const cards = wrapper.findAll("[data-test=offer]");
    expect(cards[1]?.text()).toContain("vue 2 fois");
    await cards[1]?.trigger("click");

    const detail = wrapper.find("[data-test=offer-detail]");
    expect(detail.find("h2").text()).toBe("DevOps");
    expect(detail.text()).toContain("80–100 %");
    const links = detail.findAll(".actions a");
    expect(links.map((a) => a.text())).toEqual(["Voir sur jobup", "Voir sur Indeed"]);
    expect(links.every((a) => a.attributes("rel") === "noopener noreferrer")).toBe(true);
  });
});
