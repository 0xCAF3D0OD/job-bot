import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AlertsPanel from "./AlertsPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const PATCH = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const cell = (site: string, extra: Record<string, unknown> = {}) => ({
  site,
  url: `https://${site}.example/?term=DevOps`,
  status: "todo",
  received_at: null,
  created_at: null,
  ...extra,
});

function page(extra: Record<string, unknown> = {}) {
  return {
    mailbox: "moi@exemple.ch",
    folder: "job-bot",
    sites: [
      { slug: "jobup", name: "jobup", senders: ["info@jobup.ch"], prefilled: true },
      { slug: "linkedin", name: "LinkedIn", senders: [], prefilled: true },
    ],
    searches: [
      {
        id: 1,
        terms: "DevOps",
        location: "Lausanne",
        active: true,
        cells: [cell("jobup", { status: "received", received_at: "2026-10-06T08:00:00Z" }), cell("linkedin")],
      },
    ],
    ...extra,
  };
}

describe("AlertsPanel (docs/20 §1)", () => {
  it("recherche × sites : lien, état, « J'ai créé l'alerte »", async () => {
    GET.mockResolvedValue({ data: page() });
    PUT.mockResolvedValue({ data: page() });
    const wrapper = mount(AlertsPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=mailbox]").text()).toContain("moi@exemple.ch");
    const jobup = wrapper.find("[data-test=cell-jobup]");
    expect(jobup.text()).toContain("reçue le 6 octobre");
    expect(jobup.find("a").exists()).toBe(false);
    const linkedin = wrapper.find("[data-test=cell-linkedin]");
    expect(linkedin.find("a").attributes("href")).toBe("https://linkedin.example/?term=DevOps");
    expect(linkedin.find("a").attributes("target")).toBe("_blank");
    expect(linkedin.text()).toContain("à créer");
    await wrapper.find("[data-test=created-linkedin]").setValue(true);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/alert-searches/{search_id}/sites/{site}", {
      params: { path: { search_id: 1, site: "linkedin" } },
    });
  });

  it("ajout d'une recherche, mise de côté", async () => {
    GET.mockResolvedValue({ data: page() });
    POST.mockResolvedValue({ data: page() });
    PATCH.mockResolvedValue({ data: page({ searches: [{ ...page().searches[0], active: false }] }) });
    const wrapper = mount(AlertsPanel);
    await flushPromises();
    await wrapper.find("[data-test=add-alert]").trigger("click");
    await wrapper.find("[data-test=alert-terms]").setValue(" SRE ");
    await wrapper.find("[data-test=add-alert-search]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "SRE", location: null } });
    await wrapper.find("[data-test=pause]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=alert-search]")).toHaveLength(0);
    expect(wrapper.text()).toContain("Recherches mises de côté (1)");
  });
});
