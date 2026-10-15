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
    journey: [
      { key: "alerts", done: true },
      { key: "triage", done: true },
      { key: "apply", done: false },
      { key: "follow", done: false },
      { key: "orp", done: false },
    ],
    journey_dismissed: false,
    to_review: 12,
    month: "2026-10",
    month_count: 3,
    month_target: 20,
    to_follow_up: 2,
    orp_due_month: "2026-09",
    orp_due_date: "2026-10-05",
    last_collect_at: null,
    week: [
      { day: "2026-10-09", offers: 3, applications: 0 },
      { day: "2026-10-10", offers: 0, applications: 1 },
      { day: "2026-10-11", offers: 0, applications: 0 },
      { day: "2026-10-12", offers: 2, applications: 0 },
      { day: "2026-10-13", offers: 4, applications: 1 },
      { day: "2026-10-14", offers: 1, applications: 0 },
      { day: "2026-10-15", offers: 5, applications: 1 },
    ],
    orp_history: [
      { month: "2026-07", count: 22 },
      { month: "2026-08", count: 12 },
      { month: "2026-09", count: 20 },
    ],
    ...extra,
  };
}

function mockGet(day: unknown): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/today"
          ? day
          : { items: [{ id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne", score: 82, first_seen_at: "2026-10-14T08:00:00Z", links: [] }] },
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
    expect(wrapper.find("[data-test=step-imap]").text()).toContain("réglage d'installation");
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

describe("TodayView par catégories (docs/19 §3)", () => {
  it("candidatures commencées, actualités du domaine, formations", async () => {
    GET.mockImplementation((path: string, opts?: { params?: { query?: Record<string, unknown> } }) => {
      const query = opts?.params?.query ?? {};
      if (path === "/api/today") return Promise.resolve({ data: today() });
      if (path === "/api/offers" && query.view === "in_progress")
        return Promise.resolve({
          data: {
            items: [
              { id: 7, title: "SRE", company: "Beta SA", status: "preparing" },
              { id: 8, title: "Envoyée", company: "Gamma", status: "applied" },
            ],
          },
        });
      if (path === "/api/offers") return Promise.resolve({ data: { items: [] } });
      if (path === "/api/news")
        // « Mon domaine » ne trouve rien : celles qui parlent d'emploi.
        return Promise.resolve({
          data: {
            items: query.domain_only || query.topic !== "jobs"
              ? []
              : [{ id: 1, title: "Chômage stable", url: "https://x.example/1", source: "SECO", published_at: "2026-10-06T08:00:00Z", matched: [] }],
          },
        });
      return Promise.resolve({
        data: {
          items: [
            { id: 3, title: "CKA", provider: "Linux Foundation", verified: true, url: "https://t.example", mark: { status: "in_progress", progress: "module 4/12" } },
            { id: 4, title: "Terraform Associate", provider: "HashiCorp", verified: true, url: "https://h.example", mark: null },
          ],
        },
      });
    });
    const wrapper = await mountView();
    const preparing = wrapper.find("[data-test=preparing]");
    expect(preparing.text()).toContain("SRE");
    expect(preparing.text()).not.toContain("Envoyée");
    expect(preparing.find("a").attributes("href")).toBe("/candidatures/offres/7/preparer");
    expect(wrapper.find("[data-test=today-news]").text()).toContain("Chômage stable");
    const trainings = wrapper.find("[data-test=today-trainings]").text();
    expect(trainings).toContain("module 4/12");
    expect(wrapper.find("[data-test=training-idea]").text()).toContain("Terraform Associate");
  });
});

describe("Comment ça marche (docs/21 §3)", () => {
  it("cinq étapes cochées, avec où les faire, masquables", async () => {
    mockGet(today());
    PUT.mockResolvedValue({});
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=journey]");
    expect(card.findAll("li")).toHaveLength(5);
    expect(wrapper.find("[data-test=journey-alerts]").classes()).toContain("done");
    expect(wrapper.find("[data-test=journey-apply]").classes()).not.toContain("done");
    expect(wrapper.find("[data-test=journey-orp] a").attributes("href")).toBe("/candidatures/suivi");
    expect(wrapper.find("[data-test=journey-alerts]").text()).toContain("Candidatures › Alertes");
    await wrapper.find("[data-test=dismiss-journey]").trigger("click");
    expect(PUT).toHaveBeenCalledWith("/api/journey", { body: { dismissed: true } });
  });
});

describe("Aujourd'hui, revue des pages (docs/43)", () => {
  const isoIn = (days: number): string => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };

  it("le plus urgent en tête, une seule case en orange, contacts dans « à relancer »", async () => {
    const soon = new Date(Date.now() + 3 * 3600_000).toISOString();
    mockGet(
      today({
        orp_due_date: isoIn(2),
        contacts_to_follow_up: 1,
        upcoming_interviews: [{ application_id: 4, company: "Bientôt SA", at: soon }],
      }),
    );
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=upcoming-interview]").text()).toMatch(/^Entretien (aujourd'hui|demain) à .* chez Bientôt SA/);
    expect(wrapper.find("[data-test=orp-urgent]").text()).toContain("à remettre dans 2 jours");
    expect(wrapper.find("[data-test=stat-orp]").classes()).toContain("warn");
    expect(wrapper.find("[data-test=stat-follow-up]").classes()).not.toContain("warn");
    expect(wrapper.find("[data-test=stat-follow-up]").text()).toContain("dont 1 contact");
    expect(wrapper.find("[data-test=contacts-to-follow-up]").exists()).toBe(false);
  });

  it("remise ORP lointaine : la relance passe en orange, pas d'urgence ORP ; guides en bas", async () => {
    mockGet(today({ orp_due_date: isoIn(20) }));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=orp-urgent]").exists()).toBe(false);
    expect(wrapper.find("[data-test=stat-follow-up]").classes()).toContain("warn");
    expect(wrapper.find("[data-test=stat-orp]").classes()).not.toContain("warn");
    const html = wrapper.html();
    expect(html.indexOf('data-test="journey"')).toBeGreaterThan(html.indexOf('data-test="stat-review"'));
  });

  it("aucune actualité utile : la section disparaît", async () => {
    mockGet(today());
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today() : { items: [] } }),
    );
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=today-news]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Comprendre le marché");
  });

  it("tableau de bord : tuiles avec la semaine, barres, jauge ORP et mois précédents (docs/54)", async () => {
    mockGet(today());
    const wrapper = await mountView();
    const review = wrapper.find("[data-test=stat-review]");
    expect(review.classes()).toContain("accent");
    expect(review.text()).toContain("+15 cette semaine");
    expect(review.find(".sparkline").exists()).toBe(true);
    expect(wrapper.find("[data-test=stat-month]").text()).toContain("+3 cette semaine");

    const chart = wrapper.find("[data-test=week-chart]");
    expect(chart.findAll("[data-test=week-bar]")).toHaveLength(7);
    expect(chart.text()).toContain("15 offres sur 7 jours");
    await chart.find("[data-test=week-applications]").trigger("click");
    expect(chart.text()).toContain("3 candidatures sur 7 jours");
    await chart.findAll("li")[6]!.trigger("focus");
    expect(chart.find(".bar-tip").text()).toContain("1 candidature");

    const gauge = wrapper.find("[data-test=orp-gauge]");
    expect(gauge.find("[data-test=gauge-count]").text()).toBe("3");
    expect(gauge.text()).toContain("sur 20");
    expect(gauge.findAll(".gauge-history li").map((li) => li.classes())).toEqual([["ok"], ["short"], ["ok"]]);

    // Le tableau : les mieux notées d'abord, les commencées dans le second onglet.
    const table = wrapper.find("[data-test=best]");
    expect(table.text()).toContain("Ingénieur DevOps");
    const shown = () => (table.find("[data-test=preparing]").element as HTMLElement).style.display !== "none";
    expect(shown()).toBe(false);
    await table.find("[data-test=tab-preparing]").trigger("click");
    expect(shown()).toBe(true);
  });

  it("clic direct : la ligne ouvre l'offre, la jauge le Suivi du mois, sans « › » (docs/57)", async () => {
    mockGet(today());
    const wrapper = await mountView();
    const router = wrapper.vm.$router;
    expect(wrapper.find("[data-test=best]").text()).not.toContain("›");
    expect(wrapper.text()).not.toContain("Continuer ›");
    const row = wrapper.find("[data-test=best] tr.row-link");
    await row.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/candidatures/offres");
    expect(router.currentRoute.value.query.offre).toBeDefined();
    const gauge = wrapper.find("[data-test=orp-gauge]");
    expect(gauge.element.tagName).toBe("A");
    expect(gauge.attributes("href")).toContain("/candidatures/suivi?mois=");
  });

  it("prise en main : l'étape à faire en grand, avec son illustration (docs/58)", async () => {
    mockGet(today());
    const wrapper = await mountView();
    const next = wrapper.find("[data-test=checklist-next]");
    expect(next.text()).toContain("Étape 3 sur 6");
    expect(next.text()).toContain("Saisir tes coordonnées");
    expect(next.attributes("href")).toBe("/profil?onglet=coordonnees");
    expect(next.find("[data-illustration=profile]").exists()).toBe(true);
    const journey = wrapper.find("[data-test=journey-next]");
    expect(journey.text()).toContain("Préparer lettre et CV");
    expect(journey.find("[data-illustration=message-sent]").exists()).toBe(true);
  });
});
