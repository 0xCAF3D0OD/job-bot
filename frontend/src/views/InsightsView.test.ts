import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import InsightsView from "./InsightsView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

const group = (key: string, responses: number, total: number) => ({
  key,
  label: key,
  responses,
  total,
  enough: total >= 5,
});

function report(extra: Record<string, unknown> = {}) {
  return {
    start: "2026-08-01",
    end: "2026-10-15",
    funnel: { received: 75, retained: 19, applications: 22, responses: 9, interviews: 3, engagements: 0 },
    delay: { typical: 9, shortest: 2, longest: 18 },
    comparisons: [
      { key: "source", title: "D'où vient l'offre", groups: [group("jobup", 5, 9), group("LinkedIn", 1, 3)] },
      { key: "score", title: "Note de l'IA", groups: [] },
      { key: "contact", title: "Contact dans l'entreprise", groups: [group("avec un contact", 1, 5)] },
      { key: "follow_up", title: "Relance (après 10 jours)", groups: [group("relancées", 0, 4)] },
    ],
    headline: "Les offres de jobup obtiennent plus souvent une réponse (5 sur 9, contre 1 sur 7).",
    orp_summary: null,
    unit: "month",
    buckets: [
      { start: "2026-08-01", applications: 8, responses: 3 },
      { start: "2026-09-01", applications: 10, responses: 5 },
      { start: "2026-10-01", applications: 4, responses: 1 },
    ],
    interviews_upcoming: 1,
    ...extra,
  };
}

async function mountView(path = "/candidatures/bilan") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures/bilan", component: InsightsView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(InsightsView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Bilan (docs/42, docs/55)", () => {
  it("parcours, délai, phrase de tête et groupes trop petits", async () => {
    GET.mockResolvedValue({ data: report() });
    const { wrapper } = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/insights", { params: { query: { period: "recent" } } });
    expect(wrapper.find("[data-test=funnel-received]").text()).toContain("75");
    expect(wrapper.find("[data-test=funnel-engagements]").text()).toContain("0");
    // Tuiles (docs/55) : candidatures, réponses, entretiens, délai.
    expect(wrapper.find("[data-test=tile-applications]").text()).toContain("sur 19 offres retenues");
    expect(wrapper.find("[data-test=tile-responses]").text()).toContain("41 % des envois");
    expect(wrapper.find("[data-test=tile-interviews]").text()).toContain("dont 1 à venir");
    expect(wrapper.find("[data-test=delay]").text()).toContain("9 j");
    expect(wrapper.find("[data-test=delay]").text()).toContain("de réponse, de 2 à 18 j");
    expect(wrapper.findAll("[data-test=period-bucket]")).toHaveLength(3);
    expect(wrapper.find("[data-test=period-bucket]").attributes("aria-label")).toBe(
      "août 2026 : 8 candidatures, 3 réponses",
    );
    expect(wrapper.find("[data-test=headline]").text()).toContain("jobup");
    const jobup = wrapper.find("[data-test=comparison-source] [data-test=group-jobup]");
    expect(jobup.text()).toContain("5 sur 9");
    expect(jobup.classes()).not.toContain("few");
    const linkedin = wrapper.find("[data-test=group-LinkedIn]");
    expect(linkedin.classes()).toContain("few");
    expect(linkedin.text()).toContain("trop peu pour conclure");
    expect(wrapper.find("[data-test=comparison-score]").text()).toContain("Rien à comparer");
    // Pas de résumé ORP hors d'un mois choisi.
    expect(wrapper.find("[data-test=orp-summary]").exists()).toBe(false);
  });

  it("un mois : navigation et résumé pour l'ORP à copier", async () => {
    const summary = "Octobre 2026 : 4 candidatures. 2 réponses, aucun entretien, pas encore d'engagement.";
    const weeks = [
      { start: "2026-10-01", applications: 2, responses: 1 },
      { start: "2026-10-05", applications: 2, responses: 1 },
    ];
    GET.mockResolvedValue({ data: report({ orp_summary: summary, headline: null, unit: "week", buckets: weeks }) });
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const { wrapper, router } = await mountView("/candidatures/bilan?mois=2026-10");
    expect(GET).toHaveBeenCalledWith("/api/insights", { params: { query: { period: "month", month: "2026-10" } } });
    expect(wrapper.find("[data-test=headline]").exists()).toBe(false);
    // Par semaine pour un mois choisi ; le résumé est visible sans le déplier.
    expect(wrapper.find("[data-test=period-chart] h2").text()).toBe("Par semaine");
    expect(wrapper.find("[data-test=period-bucket]").attributes("aria-label")).toContain("semaine du 1 oct");
    expect(wrapper.find("[data-test=orp-summary]").text()).toContain(summary);
    await wrapper.find("[data-test=orp-summary-copy]").trigger("click");
    expect(writeText).toHaveBeenCalledWith(summary);
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.mois).toBe("2026-09");
    await wrapper.find("[data-test=period-all]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ periode: "tout" });
    expect(GET).toHaveBeenLastCalledWith("/api/insights", { params: { query: { period: "all" } } });
  });

  it("sans candidature : invite au lieu de comparaisons vides", async () => {
    const empty = { received: 3, retained: 1, applications: 0, responses: 0, interviews: 0, engagements: 0 };
    GET.mockResolvedValue({ data: report({ funnel: empty, delay: null, headline: null }) });
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=insights-empty]").exists()).toBe(true);
    expect(wrapper.find("[data-test=comparison-source]").exists()).toBe(false);
    expect(wrapper.find("[data-test=delay]").text()).toContain("pas encore de réponse");
  });

  it("panne : un message", async () => {
    GET.mockRejectedValue(new Error("réseau"));
    const { wrapper } = await mountView();
    expect(wrapper.find("[role=alert]").text()).toContain("Bilan indisponible");
  });

  it("la jauge de l'objectif ORP, quittée d'Aujourd'hui (docs/95)", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/today"
            ? { month: "2026-10", month_count: 3, month_target: 20, orp_history: [{ month: "2026-09", count: 20 }] }
            : report(),
      }),
    );
    const { wrapper } = await mountView();
    const gauge = wrapper.find("[data-test=orp-gauge]");
    expect(gauge.exists()).toBe(true);
    expect(gauge.find("[data-test=gauge-count]").text()).toBe("3");
    expect(gauge.text()).toContain("sur 20");
  });
});
