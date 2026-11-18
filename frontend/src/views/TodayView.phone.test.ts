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
    first_steps: ["cv", "criteria", "alerts", "keep", "send"].map((key) => ({ key, done: true })),
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
  // L'Accueil du téléphone et l'éventail en petit sont chargés à part.
  await vi.dynamicImportSettled();
  await flushPromises();
  return wrapper;
}

describe("Accueil du téléphone : les offres (planche AccueilV2, §40 du 17.11)", () => {
  it("après le tri du jour, les meilleures restent dans « Top du jour » ; plus rien « à trier » ; la ville sans canton", async () => {
    localStorage.setItem(`jobA1.tri.${new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" })}`, "1");
    const wrapper = await mountView(day());
    expect(wrapper.findAll("[data-test=home-top-offer]")).toHaveLength(2);
    expect(wrapper.find("[data-test=home-top-offer]").text()).toContain("Acme SA · Lausanne");
    expect(wrapper.find("[data-test=home-top-offer]").text()).not.toContain("VD");
    expect(wrapper.find("[data-test=home-band-offers]").exists()).toBe(false);
    expect(wrapper.find("[data-test=home-triage]").exists()).toBe(false);
  });
});

describe("Accueil du téléphone un jour de repos (planche AccueilV2, état « repos », textes seulement)", () => {
  it("« Jour de repos. » à la main, la phrase, « Si tu veux avancer » et les offres", async () => {
    const wrapper = await mountView(
      day({
        rhythm: { research_today: false, count: 3, target: 3, pause_until: null },
        to_follow_up: 2,
        follow_ups: [],
      }),
    );
    expect(wrapper.find("[data-test=home-title]").text()).toBe("Jour de repos.");
    expect(wrapper.find("[data-test=home-sub]").text()).toBe("Ta semaine est faite. Si tu veux avancer, une chose t’attend.");
    expect(wrapper.find("#home-todo-title").text()).toBe("Si tu veux avancer");
    expect(wrapper.findAll("[data-test=home-top-offer]")).toHaveLength(2);
  });
});

describe("Rappel des justificatifs en haut de l’Accueil (§57 du 17.11, planche AccueilJustificatif)", () => {
  const todayKey = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" });
  const LATE = { orp_due_month: "2025-10", orp_due_date: "2025-11-05" };

  it("en retard : un îlot role=status, sans prendre le focus, « Exporter » vers la page ORP du mois", async () => {
    const wrapper = await mountView(day(LATE));
    const reminder = wrapper.find("[data-test=orp-reminder]");
    expect(reminder.attributes("role")).toBe("status");
    expect(reminder.text()).toContain("Justificatifs d’octobre à remettre");
    expect(reminder.text()).toContain("Échéance passée le 5 novembre");
    expect(wrapper.find("[data-test=orp-reminder-export]").attributes("href")).toBe("/bilan/orp?mois=2025-10");
    expect(wrapper.find("[data-test=orp-reminder-close]").attributes("aria-label")).toBe("Fermer pour aujourd’hui");
    expect(document.activeElement).toBe(document.body);
  });

  it("au plus une fois par jour, et « Fermer pour aujourd’hui » le retire", async () => {
    const wrapper = await mountView(day(LATE));
    expect(localStorage.getItem("jobA1.rappel-orp")).toBe(todayKey());
    await wrapper.find("[data-test=orp-reminder-close]").trigger("click");
    expect(wrapper.find("[data-test=orp-reminder]").exists()).toBe(false);
    wrapper.unmount();
    const again = await mountView(day(LATE));
    expect(again.find("[data-test=orp-reminder]").exists()).toBe(false);
  });

  it("revient le lendemain", async () => {
    localStorage.setItem("jobA1.rappel-orp", "2000-01-01");
    const wrapper = await mountView(day(LATE));
    expect(wrapper.find("[data-test=orp-reminder]").exists()).toBe(true);
  });

  it("avant l’échéance : seulement les 5 derniers jours, « À remettre avant le … »", async () => {
    const inDays = (n: number) => {
      const d = new Date();
      d.setDate(d.getDate() + n);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    };
    const far = await mountView(day({ orp_due_month: "2025-10", orp_due_date: inDays(9) }));
    expect(far.find("[data-test=orp-reminder]").exists()).toBe(false);
    far.unmount();
    const near = await mountView(day({ orp_due_month: "2025-10", orp_due_date: inDays(3) }));
    expect(near.find("[data-test=orp-reminder]").text()).toContain("À remettre avant le");
  });

  it("rien quand aucun mois n’est à remettre (mois « Déjà remis »)", async () => {
    const wrapper = await mountView(day({ orp_due_month: null, orp_due_date: null }));
    expect(wrapper.find("[data-test=orp-reminder]").exists()).toBe(false);
    expect(localStorage.getItem("jobA1.rappel-orp")).toBeNull();
  });
});
