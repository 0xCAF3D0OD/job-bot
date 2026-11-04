import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import InsightsView from "./InsightsView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => {
  vi.useRealTimers();
  vi.resetAllMocks();
  localStorage.removeItem("jobA1.bilan-vue");
});

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
    previous_responses: 4,
    months: [
      { month: "2026-08", count: 9 },
      { month: "2026-09", count: 10 },
      { month: "2026-10", count: 7 },
    ],
    month_target: 10,
    interviews: [
      { application_id: 1, company: "Témoin Industrie SA", day: "2026-10-29", kind: "rh", state: "upcoming", rating: null },
      { application_id: 2, company: "Prototype Fintech SA", day: "2026-10-22", kind: "technique", state: "rated", rating: 4 },
      { application_id: 3, company: "Démo Data SA", day: "2026-10-14", kind: null, state: "rejected", rating: null },
    ],
    ...extra,
  };
}

// Chaque adresse reçoit sa propre réponse : le Bilan n'est servi qu'à /api/insights.
function serve(insights: Record<string, unknown> | Error, today: Record<string, unknown> | null = null) {
  GET.mockImplementation((path: string) => {
    if (path === "/api/insights") {
      return insights instanceof Error ? Promise.reject(insights) : Promise.resolve({ data: insights });
    }
    if (path === "/api/today") return Promise.resolve({ data: today ?? undefined });
    return Promise.resolve({ data: undefined });
  });
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
  it("la phrase, la carte du meilleur site, la période, les trois chiffres, Mois par mois (B13)", async () => {
    serve(report({ comparisons: [{ key: "source", title: "", groups: [group("jobs.ch", 3, 5), group("jobup.ch", 2, 10), group("LinkedIn", 1, 4)] }] }));
    const { wrapper } = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/insights", { params: { query: { period: "recent" } } });
    // La conclusion d'abord (règles §3.2), comparée au trimestre d'avant, sans redire la bande.
    expect(wrapper.find(".insights").element.firstElementChild?.getAttribute("data-test")).toBe("headline");
    expect(wrapper.find("[data-test=headline]").text()).toBe("Ta recherche avance : 9 réponses, contre 4 au trimestre d'avant.");
    expect(wrapper.find("[data-test=headline] strong").text()).toBe("avance");
    // La bande (§3) : le site qui répond le plus, contre les autres sites qui ont assez de données.
    const band = wrapper.find("[data-test=action-band]");
    expect(band.text()).toContain("jobs.ch répond 3 fois sur 5.");
    expect(band.text()).toContain("Les autres sites : 2 fois sur 10.");
    expect(wrapper.find("[data-test=action-band-action]").text()).toBe("Cibler jobs.ch dans mes alertes");
    // La période : Un mois, 3 mois, Tout ; le choix actif coché.
    const periods = wrapper.findAll(".bilan-period button");
    expect(periods.map((p) => p.text())).toEqual(["Un mois", "3 mois", "Tout"]);
    expect(periods[1]!.attributes("aria-checked")).toBe("true");
    // Sans la bande bleue (B13) : la carte seule, sous la phrase, au-dessus de la période.
    expect(band.classes()).toContain("bilan-site");
    // Trois chiffres (B13) : candidatures, réponses, entretiens ; plus de délai de réponse.
    expect(wrapper.findAll("[data-test=bilan-figures] li").map((li) => li.text())).toEqual(["22candidatures", "9réponses", "3entretiens"]);
    expect(wrapper.find("[data-test=delay]").exists()).toBe(false);
    // « Mois par mois » mène au Suivi ORP, avec l'objectif mensuel.
    const months = wrapper.find("[data-test=detail-months]");
    expect(months.attributes("href")).toBe("/bilan/orp");
    expect(months.text()).toBe("Mois par moisObjectif ORP : 10 par mois");
  });

  it("pas de bande sans site qui se détache", async () => {
    serve(report({ comparisons: [{ key: "source", title: "", groups: [group("jobs.ch", 2, 10), group("jobup.ch", 2, 10)] }] }));
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
  });

  it("la carte Parcours, puis « Ce qui marche » et « Entretiens » repliés (B13)", async () => {
    // Une date fixe : les dates des données (le 29 octobre) ne deviennent pas « aujourd'hui ».
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-22T10:00:00Z"));
    serve(report({
      comparisons: [
        { key: "source", title: "", groups: [group("jobs.ch", 3, 5), group("jobup.ch", 2, 10), group("LinkedIn", 1, 4)] },
        { key: "score", title: "", groups: [group("high", 3, 6)] },
        { key: "contact", title: "", groups: [group("with", 3, 6), group("without", 7, 20)] },
        { key: "follow_up", title: "", groups: [group("yes", 4, 8), group("no", 6, 18)] },
      ],
    }));
    const { wrapper } = await mountView();
    const rows = wrapper.findAll("[data-test=bilan-detail] .disclosure-row");
    expect(rows.map((r) => r.find(".disclosure-title").text())).toEqual(["Ce qui marche", "Entretiens"]);
    expect(rows.every((r) => r.attributes("aria-expanded") === "false")).toBe(true);
    const descriptions = wrapper.findAll("[data-test=bilan-detail] [data-test=disclosure-description]").map((d) => d.text());
    expect(descriptions).toEqual(["Une relance fait mieux répondre : 4 sur 8, contre 6 sur 18", "3 entretiens, le prochain le 29 octobre"]);
    // Parcours (maquette) : une barre par étape, à l'échelle des offres reçues ; « Postes obtenus » seulement
    // dès le premier ; l'encadré « Le plus de pertes » ; le texte pour les lecteurs d'écran (WCAG 1.1.1).
    expect(wrapper.find("[data-test=funnel] h2").text()).toBe("Parcours");
    expect(wrapper.findAll("[data-test=funnel-received] > *").map((e) => e.text())).toEqual(["Offres reçues", "", "75"]);
    expect(wrapper.find("[data-test=funnel-received] .bilan-funnel-track > span").attributes("style")).toBe("width: 100%;");
    expect(wrapper.find("[data-test=funnel-interviews] .bilan-funnel-track > span").attributes("style")).toBe("width: 4%;");
    expect(wrapper.find("[data-test=funnel-engagements]").exists()).toBe(false);
    expect(wrapper.find("[data-test=funnel-work]").text()).toBe(
      "Le plus de pertes : entre les réponses et les entretiens. À travailler : préparer les entretiens.",
    );
    expect(wrapper.find("[data-test=funnel] .visually-hidden").text()).toBe(
      "75 offres reçues, 19 gardées, 22 candidatures, 9 réponses, 3 entretiens, 0 poste obtenu.",
    );
    // Ce qui marche : par site, avec un contact, après une relance ; pas de « Par note ».
    expect(wrapper.findAll(".bilan-compare-part h3").map((h) => h.text())).toEqual(["Par site", "Avec un contact", "Après une relance"]);
    expect(wrapper.find("[data-test=comparison-score]").exists()).toBe(false);
    expect(wrapper.find("[data-test=comparison-source] [data-test=group-jobs\\.ch]").text()).toContain("3 sur 5");
    const few = wrapper.find("[data-test=group-LinkedIn]");
    expect(few.text()).toBe("LinkedIn : trop peu pour conclure (1 sur 4)");
    expect(few.find(".bilan-bar").exists()).toBe(false);
    expect(wrapper.find("[data-test=group-no]").text()).toContain("Sans relance");
    // Entretiens : date, entreprise, type, état ; puis les enseignements, sans second repliable.
    const lines = wrapper.findAll(".bilan-interview-list li");
    expect(lines[0]!.findAll("span, strong").map((e) => e.text())).toEqual([
      "29 oct.",
      "Témoin Industrie SAPremier contact (RH)",
      "Témoin Industrie SA",
      "Premier contact (RH)",
      "à venir",
    ]);
    expect(lines[1]!.text()).toContain("ressenti 4/5");
    expect(lines[2]!.text()).toContain("pas retenu");
    expect(wrapper.find(".bilan-interviews .bilan-subtitle").text()).toBe("Enseignements");
    // Pas de « Pour l'ORP » hors d'un mois choisi.
    expect(wrapper.find("[data-test=detail-orp]").exists()).toBe(false);
  });

  it("un mois : navigation et résumé pour l'ORP à copier", async () => {
    const summary = "Octobre 2026 : 4 candidatures. 2 réponses, aucun entretien, pas encore d'engagement.";
    serve(report({ orp_summary: summary, previous_responses: 9 }));
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const { wrapper, router } = await mountView("/candidatures/bilan?mois=2026-10");
    expect(GET).toHaveBeenCalledWith("/api/insights", { params: { query: { period: "month", month: "2026-10" } } });
    expect(wrapper.find("[data-test=headline]").text()).toBe("Ta recherche tient le rythme : 9 réponses, contre 9 au mois d'avant.");
    const orp = wrapper.find("[data-test=detail-orp]");
    expect(orp.find("[data-test=disclosure-description]").text()).toBe("Le résumé d'octobre à copier");
    await orp.find(".disclosure-row").trigger("click");
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
    serve(report({ funnel: empty, delay: null, headline: null }));
    const { wrapper } = await mountView();
    // L'écran vide du Bilan (planche « Illustrations ») : « Trop tôt pour conclure », l'illustration à la place du visage.
    expect(wrapper.find("[data-test=insights-empty]").text()).toContain("Trop tôt pour conclure");
    expect(wrapper.find("[data-test=insights-empty]").text()).toContain("Le Bilan se remplit avec tes premières candidatures et réponses.");
    expect(wrapper.find("[data-test=insights-empty] .illu").exists()).toBe(true);
    expect(wrapper.find("[data-test=insights-empty] .face-mark").exists()).toBe(false);
    expect(wrapper.find("[data-test=comparison-source]").exists()).toBe(false);
    // Des tuiles à zéro n'apprennent rien (docs/128 §3) : seulement l'invitation.
    expect(wrapper.find("[data-test=bilan-tiles]").exists()).toBe(false);
  });

  it("panne : un message", async () => {
    serve(new Error("réseau"));
    const { wrapper } = await mountView();
    expect(wrapper.find("[role=alert]").text()).toContain("Bilan indisponible");
  });

  it("plus de « Mois précédents » ni de jauge ORP : le Suivi ORP les montre (B13)", async () => {
    serve(report());
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=orp-gauge]").exists()).toBe(false);
    expect(GET).not.toHaveBeenCalledWith("/api/today");
  });
});
