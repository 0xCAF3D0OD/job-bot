import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { highlight } from "../newsLabels";
import NewsView from "./NewsView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const item = (id: number, kind: string, extra: Record<string, unknown> = {}) => ({
  id,
  kind,
  source: kind === "videos" ? "KodeKloud" : "SECO",
  title: `Contenu ${id}`,
  url: `https://example.ch/${id}`,
  summary: "Résumé court.",
  has_image: kind === "videos",
  published_at: "2026-10-05T08:00:00Z",
  country: "CH",
  language: "fr",
  labour_market: false,
  matched: [],
  ...extra,
});

const pageOf = (items: unknown[], extra: Record<string, unknown> = {}) => ({
  items,
  new_articles: 0,
  new_videos: 0,
  fetched_at: new Date(Date.now() - 2 * 3600_000).toISOString(),
  refreshing: false,
  countries: ["CH", "INT"],
  languages: ["en", "fr"],
  ...extra,
});

const prefs = (extra: Record<string, unknown> = {}) => ({
  domain_keywords: ["Kubernetes", "CI/CD"],
  domain_only: false,
  countries: [],
  languages: [],
  ...extra,
});

function mockApi(page: unknown, preferences: unknown = prefs()) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/news/preferences" ? preferences : page }),
  );
  POST.mockResolvedValue({ data: { queued: true } });
  PUT.mockResolvedValue({ data: preferences });
}

const newsCalls = () => GET.mock.calls.filter(([path]) => path === "/api/news");

async function mountView(path = "/actualites") {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: NewsView }] });
  await router.push(path);
  const wrapper = mount(NewsView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("NewsView", () => {
  it("articles, compteurs de nouveautés, visite enregistrée", async () => {
    mockApi(pageOf([item(1, "articles")], { new_articles: 3, new_videos: 2 }));
    const { wrapper } = await mountView();
    expect(newsCalls()[0]![1].params.query).toMatchObject({ kind: "articles", limit: 60, domain_only: false });
    const cards = wrapper.findAll("[data-test=news-item]");
    expect(cards).toHaveLength(1);
    expect(cards[0]!.attributes("target")).toBe("_blank");
    expect(cards[0]!.attributes("rel")).toContain("noopener");
    expect(cards[0]!.find("img").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-articles]").text()).toContain("3");
    expect(POST).toHaveBeenCalledWith("/api/news/seen");
    expect(wrapper.text()).toContain("Relevé il y a 2 h");
  });

  it("vidéos avec miniature servie par la plateforme", async () => {
    mockApi(pageOf([item(7, "videos")]));
    const { wrapper } = await mountView("/actualites?rubrique=videos");
    expect(newsCalls()[0]![1].params.query.kind).toBe("videos");
    expect(wrapper.find("[data-test=news-item] img").attributes("src")).toBe("/api/news/items/7/image");
  });

  it("filtres : mon domaine, pays, langue, enregistrés", async () => {
    mockApi(pageOf([item(1, "articles", { title: "Pipeline ci-cd sur Kubernetes", matched: ["Kubernetes", "CI/CD"] })]));
    const { wrapper } = await mountView();
    expect(wrapper.findAll(".news-title mark").map((m) => m.text())).toEqual(["ci-cd", "Kubernetes"]);

    await wrapper.find("[data-test=filter-domain]").trigger("click");
    await flushPromises();
    expect(newsCalls().at(-1)![1].params.query.domain_only).toBe(true);
    expect(PUT).toHaveBeenLastCalledWith("/api/news/preferences", { body: expect.objectContaining({ domain_only: true }) });

    await wrapper.findAll("[data-test=filter-country]")[0]!.trigger("click");
    await flushPromises();
    expect(newsCalls().at(-1)![1].params.query.country).toEqual(["CH"]);
    await wrapper.findAll("[data-test=filter-language]")[1]!.trigger("click");
    await flushPromises();
    expect(newsCalls().at(-1)![1].params.query.language).toEqual(["fr"]);
  });

  it("sans mots-clés : « Mon domaine » désactivé, lien vers les Réglages", async () => {
    mockApi(pageOf([]), prefs({ domain_keywords: [] }));
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=filter-domain]").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Réglages → Actualités");
  });

  it("relever maintenant, puis mise à jour pendant le relevé", async () => {
    vi.useFakeTimers();
    mockApi(pageOf([]));
    const { wrapper } = await mountView();
    await wrapper.find("[data-test=news-refresh]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/news/refresh");
    expect(wrapper.find("[data-test=news-refreshing]").exists()).toBe(true);
    const before = newsCalls().length;
    await vi.advanceTimersByTimeAsync(4_000);
    expect(newsCalls().length).toBe(before + 1);
    vi.useRealTimers();
  });
});

describe("highlight", () => {
  it("surligne sans tenir compte de la casse ni de la ponctuation des mots-clés", () => {
    expect(highlight("Le CI-CD et kubernetes", ["CI/CD", "Kubernetes"])).toEqual([
      { text: "Le ", hit: false },
      { text: "CI-CD", hit: true },
      { text: " et ", hit: false },
      { text: "kubernetes", hit: true },
    ]);
    expect(highlight("Kubernetesque", ["Kubernetes"])).toEqual([{ text: "Kubernetesque", hit: false }]);
  });
});
