import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import NewsSourcesPanel from "./NewsSourcesPanel.vue";

const GET = vi.fn();
const PUT = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const source = {
  id: 1,
  kind: "articles",
  name: "SECO",
  url: "https://www.seco.admin.ch",
  feed_url: "https://x/rss",
  match: null,
  active: true,
  country: "CH",
  language: null,
  labour_market: true,
  fetched_at: null,
  error: null,
};
const prefs = { domain_keywords: ["DevOps"], domain_only: false, countries: [], languages: [] };

describe("NewsSourcesPanel", () => {
  it("mots-clés du domaine et réglages d'une source", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/news/preferences" ? prefs : [source] }),
    );
    PUT.mockImplementation((_path: string, { body }: { body: unknown }) => Promise.resolve({ data: body }));
    PATCH.mockResolvedValue({ data: [{ ...source, country: "INT" }] });
    const wrapper = mount(NewsSourcesPanel);
    await flushPromises();

    await wrapper.find("[data-test=domain-input]").setValue("Kubernetes, CKA");
    await wrapper.find("form.inline-form").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/news/preferences", {
      body: { ...prefs, domain_keywords: ["DevOps", "Kubernetes", "CKA"] },
    });
    expect(wrapper.find("[data-test=domain-keywords]").text()).toContain("CKA");

    await wrapper.find("[data-test=source-country]").setValue("INT");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/news/sources/{source_id}", {
      params: { path: { source_id: 1 } },
      body: { country: "INT" },
    });
    expect((wrapper.find("[data-test=source-labour]").element as HTMLInputElement).checked).toBe(true);
  });
});
