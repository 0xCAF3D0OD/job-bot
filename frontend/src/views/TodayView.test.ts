import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import TodayView from "./TodayView.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    POST: vi.fn(),
  },
}));
afterEach(() => vi.resetAllMocks());

function today(extra: Record<string, unknown> = {}) {
  return {
    checklist: [
      { key: "criteria", done: true },
      { key: "profile", done: true },
      { key: "identity", done: false },
      { key: "orp_target", done: true },
      { key: "notifications", done: true },
      { key: "imap", done: false },
    ],
    checklist_dismissed: false,
    to_review: 12,
    month: "2026-10",
    month_count: 3,
    month_target: 20,
    to_follow_up: 2,
    orp_due_month: "2026-09",
    orp_due_date: "2026-10-05",
    last_collect_at: null,
    ...extra,
  };
}

function mockGet(day: unknown): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/today"
          ? day
          : { items: [{ id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne", score: 82 }] },
    }),
  );
}

async function mountView() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(TodayView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("TodayView", () => {
  it("liste de démarrage : étapes faites et liens vers ce qui manque", async () => {
    mockGet(today());
    const wrapper = await mountView();
    const checklist = wrapper.find("[data-test=checklist]");
    expect(checklist.text()).toContain("4 / 6");
    expect(wrapper.find("[data-test=step-identity] a").attributes("href")).toBe("/profil?onglet=coordonnees");
    expect(wrapper.find("[data-test=step-imap]").text()).toContain("JOBBOT_IMAP_USER");
    expect(wrapper.find("[data-test=step-criteria] a").exists()).toBe(false);
  });

  it("point du jour : offres, mois, relances, échéance ORP, meilleures offres", async () => {
    mockGet(today());
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=stat-review]").text()).toContain("12");
    expect(wrapper.find("[data-test=stat-month]").text()).toContain("3 / 20");
    expect(wrapper.find("[data-test=stat-follow-up]").text()).toContain("2");
    expect(wrapper.find("[data-test=stat-orp]").text()).toContain("5 octobre");
    expect(wrapper.text()).toContain("Ingénieur DevOps");
  });

  it("tout fait ou masqué : la liste disparaît", async () => {
    mockGet(today({ checklist_dismissed: true }));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=checklist]").exists()).toBe(false);
  });

  it("masquer la liste l'enregistre", async () => {
    mockGet(today());
    PUT.mockResolvedValue({ response: { status: 204 } });
    const wrapper = await mountView();
    await wrapper.find("[data-test=dismiss]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/onboarding", { body: { dismissed: true } });
  });
});
