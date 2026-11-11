import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { resetCvReading } from "../composables/useCvReading";
import TodayView from "./TodayView.vue";

// « Relire ton CV » en tête de « À faire » (maquette du 10 novembre, PR 22 ; AujourdhuiOrdinateurTravailD et
// AccueilSmile, variable cvNonLu).
const GET = vi.fn();
const phone = ref(false);
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn(), POST: vi.fn() }, QUIET: {} }));
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone }) }));
afterEach(() => {
  vi.resetAllMocks();
  resetCvReading();
  localStorage.clear();
});

const DAY = {
  first_steps: ["profile", "alerts", "keep", "prepare", "sent"].map((key) => ({ key, done: true })),
  first_steps_dismissed: false,
  has_offers: true,
  to_review: 0,
  month: "2026-11",
  month_count: 3,
  month_target: 10,
  to_follow_up: 2,
  week: [],
  orp_history: [],
};
const CV = { id: 3, filename: "CV.pdf", doc_type: "pdf", size: 1000, text_status: "ok", uploaded_at: "2026-11-02T09:00:00Z", chunk_count: 0, kind: null, read_state: null, read_at: null, found: null };

async function mountView(documents: unknown[]) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/today" ? DAY : path === "/api/documents" ? documents : path === "/api/insights" ? { highlight: null } : { items: [] } }),
  );
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(TodayView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("« Relire ton CV » dans Aujourd’hui (PR 22)", () => {
  it("ordinateur : première ligne de « À faire », en pêche, lien vers le Profil", async () => {
    phone.value = false;
    const wrapper = await mountView([CV]);
    const first = wrapper.findAll("[data-test=today-tasks] .today-task")[0]!;
    expect(first.attributes("data-test")).toBe("cv-unread");
    expect(first.classes()).toContain("tone-late");
    expect(first.text()).toContain("Relire ton CV");
    expect(first.text()).toContain("Sans lui, tes offres ne sont pas notées · 30 secondes");
    expect(first.attributes("href")).toBe("/profil");
  });

  it("téléphone : première ligne, icône document à la place du nombre", async () => {
    phone.value = true;
    const wrapper = await mountView([CV]);
    const first = wrapper.findAll("[data-test=home-todo] li a")[0]!;
    expect(first.attributes("data-test")).toBe("todo-cv-unread");
    expect(first.find(".home-todo-icon").exists()).toBe(true);
    expect(first.find("strong").exists()).toBe(false);
    expect(first.text()).toContain("Relire ton CV");
    expect(first.text()).toContain("Sans lui, tes offres ne sont pas notées");
  });

  it("reste pendant la lecture ; disparaît dès que le CV est lu, ou sans CV lisible", async () => {
    phone.value = false;
    for (const [documents, shown] of [
      [[{ ...CV, read_state: "reading" }], true],
      [[{ ...CV, read_state: "done", read_at: "2026-11-10T10:00:00Z", found: { competence: 3 } }], false],
      [[{ ...CV, chunk_count: 5 }], false],
      [[{ ...CV, text_status: "unreadable" }], false],
      [[], false],
    ] as [unknown[], boolean][]) {
      resetCvReading();
      const wrapper = await mountView(documents);
      expect(wrapper.find("[data-test=cv-unread]").exists()).toBe(shown);
      wrapper.unmount();
    }
  });
});
