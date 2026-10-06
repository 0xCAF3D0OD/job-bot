import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import NewsSourcesPanel from "./NewsSourcesPanel.vue";

const GET = vi.fn();
const PUT = vi.fn();
const PATCH = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    POST: (...a: unknown[]) => POST(...a),
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
  query: null,
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

const catalog = {
  domains: { emploi: "Marché et recherche d'emploi", devops: "DevOps et Kubernetes" },
  sources: [
    { id: "seco", name: "SECO", kind: "articles", url: "https://s", domains: ["emploi"], country: "CH", language: null, labour_market: true, description: "Chômage.", added: true },
    { id: "xavki", name: "xavki", kind: "videos", url: "https://x", domains: ["devops"], country: "INT", language: "fr", labour_market: false, description: "DevOps en français.", added: false },
  ],
};

function mockGet() {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data: path === "/api/news/preferences" ? prefs : path === "/api/news/catalog" ? catalog : [source],
    }),
  );
}

describe("NewsSourcesPanel — suggestions et veilles", () => {
  it("suggestions filtrées par domaine, ajout en un clic", async () => {
    mockGet();
    POST.mockResolvedValue({ data: [source, { ...source, id: 2, name: "xavki", kind: "videos" }] });
    const wrapper = mount(NewsSourcesPanel);
    await flushPromises();
    await wrapper.find("[data-test=browse-catalog]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=catalog-source]")).toHaveLength(2);
    await wrapper.find("[data-test=catalog-domain]").setValue("devops");
    const rows = wrapper.findAll("[data-test=catalog-source]");
    expect(rows).toHaveLength(1);
    expect(rows[0]!.text()).toContain("français");
    await wrapper.find("[data-test=catalog-add]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/news/catalog/{catalog_id}", { params: { path: { catalog_id: "xavki" } } });
    expect(wrapper.find("[data-test=catalog-source]").text()).toContain("suivie");
    expect(wrapper.findAll("[data-test=news-source]")).toHaveLength(2);
  });

  it("nouvelle veille : mots-clés, pays, langue", async () => {
    mockGet();
    POST.mockResolvedValue({
      data: [source, { ...source, id: 3, name: "Veille : Kubernetes emploi", query: "Kubernetes emploi" }],
    });
    const wrapper = mount(NewsSourcesPanel);
    await flushPromises();
    await wrapper.find("[data-test=add-search]").trigger("click");
    await wrapper.find("[data-test=search-query]").setValue(" Kubernetes emploi ");
    await wrapper.find("[data-test=add-news-search]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/news/searches", {
      body: { query: "Kubernetes emploi", country: "CH", language: "fr" },
    });
    expect(wrapper.text()).toContain("veille Google Actualités : « Kubernetes emploi »");
  });
});
