import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import TrainingsView from "./TrainingsView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const training = (id: number, extra: Record<string, unknown> = {}) => ({
  id,
  title: "Certified Kubernetes Administrator (CKA)",
  provider: "The Linux Foundation / CNCF",
  kind: "certification",
  format: "exam_online",
  language: "en",
  price: "paid",
  duration: null,
  level: "intermediate",
  url: `https://training.example/${id}`,
  tags: ["Kubernetes", "CKA"],
  description: "Certification de référence.",
  prep: "KodeKloud.",
  origin: "catalog",
  verified: true,
  matched: ["Kubernetes", "CKA"],
  mark: null,
  ...extra,
});

const page = (items: unknown[], extra: Record<string, unknown> = {}) => ({
  items,
  domain_keywords: ["Kubernetes", "CKA"],
  languages: ["en", "fr"],
  can_suggest: true,
  ...extra,
});

async function mountView(path = "/formations") {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: TrainingsView }] });
  await router.push(path);
  const wrapper = mount(TrainingsView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("TrainingsView", () => {
  it("catalogue filtré sur « Mon domaine », mention ORP, mots surlignés", async () => {
    GET.mockResolvedValue({ data: page([training(1), training(2, { title: "Microsoft Learn", price: "free", kind: "parcours", matched: [] })]) });
    const wrapper = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/trainings", { params: { query: { domain_only: true } } });
    expect(wrapper.find("[data-test=orp-note]").text()).toContain("accord");
    const cards = wrapper.findAll("[data-test=training]");
    expect(cards).toHaveLength(2);
    expect(cards[0]!.findAll("mark").map((m) => m.text())).toEqual(["Kubernetes", "CKA"]);
    expect(cards[0]!.text()).toContain("examen en ligne surveillé");
    expect(cards[0]!.text()).toContain("Financement possible");
    expect(cards[1]!.text()).not.toContain("Financement possible");

    await wrapper.find("[data-test=filter-price]").setValue("free");
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    await wrapper.find("[data-test=filter-all]").trigger("click");
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/api/trainings", { params: { query: { domain_only: false } } });
  });

  it("suivi : intéressé, en cours avec progression, retrait", async () => {
    GET.mockResolvedValue({ data: page([training(1)]) });
    PUT.mockImplementation((_p: string, { body }: { body: Record<string, unknown> }) =>
      Promise.resolve({ data: { progress: null, done_at: null, certified: null, ...body } }),
    );
    DELETE.mockResolvedValue({});
    const wrapper = await mountView();
    await wrapper.find("[data-test=mark-in_progress]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/trainings/{training_id}/mark", {
      params: { path: { training_id: 1 } },
      body: { status: "in_progress", progress: null, done_at: null, certified: null },
    });
    await wrapper.find("[data-test=progress]").setValue("module 4/12");
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body.progress).toBe("module 4/12");
    expect(wrapper.find("[data-test=tab-mine]").text()).toContain("1");
    await wrapper.find("[data-test=mark-in_progress]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalled();
  });

  it("suggestions de l'IA : recherche, garder, écarter", async () => {
    const ai = training(5, { title: "Kubernetes en français", origin: "ai", verified: false, price: "free" });
    GET.mockResolvedValue({ data: page([ai, training(6, { origin: "ai", verified: false, title: "Autre" })]) });
    POST.mockImplementation((path: string) =>
      Promise.resolve(path === "/api/trainings/suggest" ? { data: { added: 2 } } : {}),
    );
    const wrapper = await mountView();
    await wrapper.find("[data-test=suggest]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("2 formation(s) proposée(s)");
    expect(wrapper.findAll("[data-test=unverified]")).toHaveLength(2);
    await wrapper.findAll("[data-test=keep]")[0]!.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/trainings/{training_id}/review", { params: { path: { training_id: 5 } }, body: { keep: true } });
    await wrapper.find("[data-test=dismiss]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    expect(wrapper.findAll("[data-test=unverified]")).toHaveLength(0);
  });

  it("onglet Mes formations : seulement les formations suivies", async () => {
    GET.mockResolvedValue({ data: page([training(1, { mark: { status: "done", progress: null, done_at: "2026-09-30", certified: true } }), training(2)]) });
    const wrapper = await mountView("/formations?onglet=miennes");
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    expect((wrapper.find("[data-test=certified]").element as HTMLInputElement).checked).toBe(true);
  });
});
