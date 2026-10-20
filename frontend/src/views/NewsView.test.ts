import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { highlight } from "../newsLabels";
import NewsView from "./NewsView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  BACKGROUND: { headers: { "X-Jobbot-Background": "1" } },
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
const loggedIn = ref(true);
const me = ref<{ demo: boolean } | null>({ demo: false });
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ loggedIn, me }) }));
afterEach(() => {
  vi.resetAllMocks();
  loggedIn.value = true;
  me.value = { demo: false };
});

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
  it("modules à la RTS : en tête, deux en second rang, puis des lignes par période ; filtres derrière « Filtrer »", async () => {
    const now = Date.now();
    const at = (days: number) => new Date(now - days * 24 * 3600_000).toISOString();
    mockApi(
      pageOf([
        item(1, "articles", { published_at: at(0), source: "SECO — marché du travail" }),
        item(2, "articles", { published_at: at(0), has_image: true }),
        item(3, "articles", { published_at: at(3) }),
        item(4, "articles", { published_at: at(3) }),
        item(5, "articles", { published_at: at(20) }),
      ]),
      prefs({ countries: ["CH"] }),
    );
    const { wrapper } = await mountView();
    // En tête : la plus récente qui a une image ; les autres gardent l'ordre.
    expect(wrapper.find(".news-story.lead .news-title").text()).toBe("Contenu 2");
    expect(wrapper.find(".news-top").classes()).toContain("count-3");
    expect(wrapper.findAll(".news-story.second .news-title").map((t) => t.text())).toEqual(["Contenu 1", "Contenu 3"]);
    // Sans image : une vignette texte avec le nom court de la source.
    expect(wrapper.find(".news-story.second .news-thumb.text").text()).toBe("SECO");
    expect(wrapper.findAll(".news-group-title").map((h) => h.text())).toEqual(["Cette semaine", "Plus ancien"]);
    expect(wrapper.find(".news-story.row .news-time").text()).toMatch(/^il y a|hier/);
    const toggle = wrapper.find("[data-test=news-filter-toggle]");
    expect(toggle.attributes("aria-label")).toBe("Filtrer, 1 actif");
    expect(toggle.find("[data-test=news-filter-count]").text()).toBe("1");
    expect((wrapper.find("[data-test=news-filter-popover]").element as HTMLElement).style.display).toBe("none");
    await toggle.trigger("click");
    expect((wrapper.find("[data-test=news-filter-popover]").element as HTMLElement).style.display).toBe("");
  });

  it("une seule actualité : en tête sur toute la largeur ; téléphone : seule l'actualité en tête est en grand", async () => {
    mockApi(pageOf([item(1, "articles", { has_image: true })]));
    const { wrapper } = await mountView();
    expect(wrapper.find(".news-top").classes()).toContain("count-1");
    expect(wrapper.find(".news-second").exists()).toBe(false);

    const original = globalThis.matchMedia;
    globalThis.matchMedia = ((query: string) =>
      ({ matches: true, media: query, addEventListener: () => {}, removeEventListener: () => {} }) as unknown as MediaQueryList);
    try {
      mockApi(pageOf([item(1, "articles", { has_image: true }), item(2, "articles"), item(3, "articles")]));
      const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: NewsView }] });
      await router.push("/actualites");
      const phone = mount(NewsView, { global: { plugins: [router], stubs: { teleport: true } } });
      await flushPromises();
      expect(phone.find(".news-top").classes()).toContain("count-1");
      expect(phone.findAll(".news-story.row")).toHaveLength(2);
    } finally {
      globalThis.matchMedia = original;
    }
  });

  it("articles, compteurs de nouveautés, visite enregistrée", async () => {
    mockApi(pageOf([item(1, "articles")], { new_articles: 4, new_jobs: 3, new_economy: 1, new_videos: 2 }));
    const { wrapper } = await mountView();
    expect(newsCalls()[0]![1].params.query).toMatchObject({ kind: "articles", topic: "jobs", limit: 60, domain_only: false });
    const cards = wrapper.findAll("[data-test=news-item]");
    expect(cards).toHaveLength(1);
    expect(cards[0]!.attributes("target")).toBe("_blank");
    expect(cards[0]!.attributes("rel")).toContain("noopener");
    expect(cards[0]!.find("img").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-articles]").text()).toContain("3");
    expect(wrapper.find("[data-test=tab-economy]").text()).toContain("1");
    // Une écriture de la page elle-même : sans message pendant une maintenance (docs/81 §2).
    expect(POST).toHaveBeenCalledWith("/api/news/seen", { headers: { "X-Jobbot-Background": "1" } });
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

  it("sans mots-clés : « Mon domaine » ouvre le champ sur place (docs/43 n° 4)", async () => {
    mockApi(pageOf([]), prefs({ domain_keywords: [] }));
    PUT.mockImplementation((_path: string, { body }: { body: unknown }) => Promise.resolve({ data: body }));
    const { wrapper } = await mountView();
    expect(wrapper.text()).not.toContain("Réglages → Actualités");
    await wrapper.find("[data-test=filter-domain]").trigger("click");
    await wrapper.find("[data-test=domain-field-input]").setValue("DevOps, Kubernetes");
    await wrapper.find("[data-test=domain-field]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/news/preferences", {
      body: expect.objectContaining({ domain_keywords: ["DevOps", "Kubernetes"], domain_only: true }),
    });
    expect(wrapper.find("[data-test=domain-field]").exists()).toBe(false);
    expect(newsCalls().at(-1)![1].params.query.domain_only).toBe(true);
  });

  it("économie : l'autre onglet des articles (docs/43 n° 16)", async () => {
    mockApi(pageOf([item(1, "articles")]));
    await mountView("/actualites?rubrique=economie");
    expect(newsCalls()[0]![1].params.query).toMatchObject({ kind: "articles", topic: "economy" });
  });

  it("téléphone : 10 contenus, puis « Voir plus » (docs/43 n° 17)", async () => {
    const original = globalThis.matchMedia;
    globalThis.matchMedia = ((query: string) =>
      ({ matches: true, media: query, addEventListener: () => {}, removeEventListener: () => {} }) as unknown as MediaQueryList);
    try {
      mockApi(pageOf(Array.from({ length: 20 }, (_, n) => item(n + 1, "articles"))));
      const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: NewsView }] });
      await router.push("/actualites");
      const wrapper = mount(NewsView, { global: { plugins: [router], stubs: { teleport: true } } });
      await flushPromises();
      expect(wrapper.findAll("[data-test=news-item]")).toHaveLength(10);
      await wrapper.find("[data-test=news-more]").trigger("click");
      expect(wrapper.findAll("[data-test=news-item]")).toHaveLength(20);
      expect(wrapper.find("[data-test=news-more]").exists()).toBe(false);
    } finally {
      globalThis.matchMedia = original;
    }
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

  it("dans la démo : la visite n'enregistre rien, donc pas de message de refus", async () => {
    me.value = { demo: true };
    mockApi(pageOf([item(1, "articles")], { new_articles: 3 }));
    await mountView();
    expect(POST).not.toHaveBeenCalledWith("/api/news/seen", expect.anything());
  });

  it("sans connexion : lecture seule, rien n'est enregistré", async () => {
    loggedIn.value = false;
    mockApi(pageOf([item(1, "articles")], { new_articles: 3 }));
    const { wrapper } = await mountView();
    expect(POST).not.toHaveBeenCalledWith("/api/news/seen", expect.anything());
    await wrapper.find("[data-test=filter-domain]").trigger("click");
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(newsCalls().at(-1)![1].params.query.domain_only).toBe(true);
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
