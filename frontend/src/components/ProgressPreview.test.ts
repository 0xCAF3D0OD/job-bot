import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) }, BACKGROUND: {} }));
const count = ref(3);
const reset = vi.fn(() => (count.value = 0));
vi.mock("../composables/useNewsCount", () => ({ useNewsCount: () => ({ count, reset }) }));
const me = ref({ demo: false });
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me }) }));

import ProgressPreview from "./ProgressPreview.vue";

const article = (id: number, matched: string[] = ["kubernetes"]) => ({
  id,
  title: `Article ${id}`,
  url: `https://exemple.ch/${id}`,
  source: "Le Temps",
  published_at: "2026-10-18T08:00:00Z",
  has_image: false,
  matched,
});

function answer(trainings: unknown[]) {
  GET.mockImplementation((path: string) => {
    if (path === "/api/news") return Promise.resolve({ data: { items: [article(1), article(2), article(3)] } });
    if (path === "/api/trainings") return Promise.resolve({ data: { items: trainings } });
    return Promise.resolve({ data: null });
  });
}

async function mountAt(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push(path);
  return mount(ProgressPreview, { global: { plugins: [router] } });
}

afterEach(() => {
  GET.mockReset();
  POST.mockReset();
  reset.mockClear();
  count.value = 3;
  me.value = { demo: false };
});

describe("Progresser dans la capsule (docs/92)", () => {
  it("le livre ouvre l'aperçu : actualités, formations en cours, liens ; le point s'efface", async () => {
    answer([
      { id: 7, title: "CKA", provider: "CNCF", mark: { status: "in_progress", progress: "Module 3 sur 6" } },
      { id: 8, title: "AWS", provider: "AWS", mark: { status: "interested" } },
    ]);
    POST.mockResolvedValue({});
    const wrapper = await mountAt("/aujourdhui");
    const zone = wrapper.find("[data-test=progress-zone]");
    expect(wrapper.find("[data-test=progress-dot]").exists()).toBe(true);
    expect(zone.attributes("aria-label")).toBe("Progresser, du nouveau à lire");
    await zone.trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=preview-news]")).toHaveLength(3);
    const trainings = wrapper.find("[data-test=preview-trainings]");
    expect(trainings.text()).toContain("Module 3 sur 6");
    expect(trainings.text()).not.toContain("AWS");
    expect(trainings.find("a").attributes("href")).toBe("/progresser/formations?onglet=miennes&formation=7");
    expect(wrapper.find("[data-test=preview-all-news]").attributes("href")).toBe("/progresser/actualites");
    expect(reset).toHaveBeenCalled();
    expect(POST).toHaveBeenCalledWith("/api/news/seen", {});
    expect(wrapper.find("[data-test=progress-dot]").exists()).toBe(false);
  });

  it("sans formation en cours, la section disparaît ; dans la démo, rien n'est enregistré", async () => {
    answer([]);
    me.value = { demo: true };
    const wrapper = await mountAt("/progresser/actualites");
    expect(wrapper.find("[data-test=progress-zone]").classes()).toContain("active");
    await wrapper.find("[data-test=progress-zone]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=preview-trainings]").exists()).toBe(false);
    expect(reset).toHaveBeenCalled();
    expect(POST).not.toHaveBeenCalled();
  });
});
