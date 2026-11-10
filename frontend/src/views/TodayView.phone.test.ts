import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import TodayView from "./TodayView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn(), POST: vi.fn() } }));
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone: ref(true) }) }));
afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

const OFFER = { id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne, VD", score: 82, links: [] };
function day(extra: Record<string, unknown> = {}) {
  return {
    first_steps: ["profile", "alerts", "keep", "prepare", "sent"].map((key) => ({ key, done: true })),
    first_steps_dismissed: false,
    has_offers: true,
    to_review: 12,
    month: "2026-11",
    month_count: 3,
    month_target: 10,
    to_follow_up: 0,
    week: [],
    orp_history: [],
    ...extra,
  };
}
async function mountView(today: unknown) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/today" ? today : path === "/api/insights" ? { highlight: null } : { items: [OFFER, { ...OFFER, id: 2 }] } }),
  );
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(TodayView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("Accueil du téléphone : les cartes Offres (maquette AccueilSmile)", () => {
  it("restent là après le tri du jour, tant qu’il reste des offres ; la ville sans canton", async () => {
    localStorage.setItem(`jobA1.tri.${new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" })}`, "1");
    const wrapper = await mountView(day());
    expect(wrapper.findAll("[data-test=home-card]")).toHaveLength(2);
    expect(wrapper.find("[data-test=home-card]").text()).toContain("Acme SA · Lausanne");
    expect(wrapper.find("[data-test=home-card]").text()).not.toContain("VD");
    expect(wrapper.find("[data-test=home-triage]").exists()).toBe(false);
  });
});
