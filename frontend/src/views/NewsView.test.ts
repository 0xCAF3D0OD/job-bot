import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import NewsView from "./NewsView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
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
  ...extra,
});

async function mountView(path = "/actualites") {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: NewsView }] });
  await router.push(path);
  const wrapper = mount(NewsView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("NewsView", () => {
  it("articles, compteurs de nouveautés, visite enregistrée", async () => {
    GET.mockResolvedValue({ data: { items: [item(1, "articles")], new_articles: 3, new_videos: 2 } });
    POST.mockResolvedValue({ data: {} });
    const { wrapper } = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/news", { params: { query: { kind: "articles", limit: 60 } } });
    const cards = wrapper.findAll("[data-test=news-item]");
    expect(cards).toHaveLength(1);
    expect(cards[0]!.attributes("target")).toBe("_blank");
    expect(cards[0]!.attributes("rel")).toContain("noopener");
    expect(cards[0]!.find("img").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-articles]").text()).toContain("3");
    expect(POST).toHaveBeenCalledWith("/api/news/seen");
  });

  it("vidéos avec miniature servie par la plateforme", async () => {
    GET.mockResolvedValue({ data: { items: [item(7, "videos")], new_articles: 0, new_videos: 0 } });
    POST.mockResolvedValue({ data: {} });
    const { wrapper } = await mountView("/actualites?rubrique=videos");
    expect(GET).toHaveBeenCalledWith("/api/news", { params: { query: { kind: "videos", limit: 60 } } });
    expect(wrapper.find("[data-test=news-item] img").attributes("src")).toBe("/api/news/items/7/image");
  });

  it("vide : renvoie vers les Réglages", async () => {
    GET.mockResolvedValue({ data: { items: [], new_articles: 0, new_videos: 0 } });
    POST.mockResolvedValue({ data: {} });
    const { wrapper } = await mountView();
    expect(wrapper.text()).toContain("Gérer les sources");
  });
});
