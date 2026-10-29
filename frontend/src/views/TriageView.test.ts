// L'écran de tri des offres du jour (1.6.50, revue 1.6.46).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import TriageView from "./TriageView.vue";

const GET = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PATCH: (...a: unknown[]) => PATCH(...a) },
}));
afterEach(() => vi.resetAllMocks());

const offer = (id: number, title: string, score: number) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne",
  score,
  why: "Ta plateforme colle.",
  keywords_asks: [],
  links: [],
});
// Un mois déjà atteint : jamais en retard, la dose reste à 3 quel que soit le jour où le test tourne.
const TODAY = { month_count: 10, month_target: 10, month: "2026-10", rhythm: { research_today: true } };

function mockApi(offers: unknown[], today: Record<string, unknown> = TODAY): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/today" ? today : { items: offers } }),
  );
}

async function mountTriage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/aujourdhui", name: "today", component: { template: "<div />" } },
      { path: "/aujourdhui/tri", name: "triage", component: TriageView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/aujourdhui/tri");
  const wrapper = mount(TriageView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("L'écran de tri (1.6.50)", () => {
  it("« ← Aujourd'hui », le titre, « 1 sur 3 », une offre à la fois", async () => {
    mockApi([offer(1, "DevOps", 90), offer(2, "SRE", 80), offer(3, "Cloud", 75), offer(4, "Data", 70)]);
    const { wrapper } = await mountTriage();
    expect(wrapper.find("h1").text()).toBe("Offres du jour");
    expect(wrapper.find("[data-test=triage-back]").attributes("href")).toBe("/aujourdhui");
    // La dose du jour : 3 offres (5 si le mois est en retard), comme Aujourd'hui.
    // La progression remplace la phrase « 3 offres à trier. ».
    expect(wrapper.text()).not.toContain("à trier");
    expect(wrapper.find("[data-test=step-progress]").text()).toBe("1 sur 3");
    expect(wrapper.findAll("[data-test=pick-card]")).toHaveLength(1);
    // Garder : la progression suit.
    await wrapper.find("[data-test=pick-keep]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=step-progress]").text()).toBe("2 sur 3");
  });

  it("le tri fini : l'illustration, le récapitulatif, « Revenir à Aujourd'hui » sans offre gardée", async () => {
    mockApi([offer(1, "DevOps", 90)]);
    const { wrapper } = await mountTriage();
    await wrapper.find("[data-test=pick-dismiss]").trigger("click");
    await flushPromises();
    const done = wrapper.find("[data-test=pick-done]");
    expect(done.text()).toContain("Tri du jour terminé");
    expect(done.text()).toContain("1 écartée.");
    expect(wrapper.find("[data-test=step-progress]").exists()).toBe(false);
    expect(wrapper.find("[data-test=pick-today]").attributes("href")).toBe("/aujourdhui");
  });

  it("rien à trier, ou un jour de repos : un écran vide qui dit pourquoi", async () => {
    mockApi([]);
    const empty = (await mountTriage()).wrapper;
    expect(empty.find("[data-test=triage-empty]").text()).toContain("Rien à trier");
    mockApi([offer(1, "DevOps", 90)], { ...TODAY, rhythm: { research_today: false } });
    const rest = (await mountTriage()).wrapper;
    expect(rest.find("[data-test=triage-empty]").text()).toContain("Jour de repos");
  });
});
