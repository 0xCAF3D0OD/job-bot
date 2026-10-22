import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { UNDO_MS } from "../composables/useUndo";
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

const STEP_KEYS = ["profile", "alerts", "keep", "prepare", "sent"] as const;
// Un compte neuf : les `done` premières étapes faites.
function starting(done: number, extra: Record<string, unknown> = {}) {
  return today({ first_steps: STEP_KEYS.map((key, i) => ({ key, done: i < done })), ...extra });
}

function today(extra: Record<string, unknown> = {}) {
  return {
    first_steps: STEP_KEYS.map((key) => ({ key, done: true })),
    first_steps_dismissed: false,
    has_offers: true,
    first_steps_offer_id: null,
    first_steps_finished: false,
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

describe("Les premiers pas (docs/128)", () => {
  it("une seule prochaine action, à la place de la phrase du jour", async () => {
    mockGet(starting(1));
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=first-steps]");
    expect(card.text()).toContain("2 sur 5");
    expect(card.find("h2").text()).toBe("Alertes sur les sites d'emploi");
    expect(card.find("[data-test=first-steps-action]").attributes("href")).toBe("/candidatures/alertes");
    expect(wrapper.find("[data-test=first-step-profile]").classes()).toContain("done");
    expect(wrapper.find("[data-test=first-step-alerts]").classes()).toContain("current");
    expect(wrapper.find("[data-test=today-sentence]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-cta]").exists()).toBe(false);
    // Les anciens guides ont disparu.
    expect(wrapper.find("[data-test=checklist]").exists()).toBe(false);
    expect(wrapper.find("[data-test=journey]").exists()).toBe(false);
  });

  it("alertes créées, aucune offre encore : on attend, ou on en ajoute une", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? starting(2, { has_offers: false, to_review: 0, to_follow_up: 0, follow_ups: [] }) : { items: [] } }),
    );
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=first-steps]");
    expect(card.find("h2").text()).toBe("Alertes prêtes");
    expect(card.text()).toContain("d'ici un ou deux jours");
    expect(card.find("[data-test=first-steps-add]").attributes("href")).toBe("/candidatures/offres?ajouter=1");
    // Rien dans « À faire » : la carte ne s'affiche pas ; le mois ORP reste.
    expect(wrapper.find("[data-test=best]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-month]").exists()).toBe(true);
    expect(wrapper.find("[data-test=today-calm]").exists()).toBe(false);
  });

  it("garder une offre : le bouton descend sur les offres du jour", async () => {
    mockGet(starting(2));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=first-steps-action]").attributes("href")).toBe("/aujourdhui#offres-du-jour");
    expect(wrapper.find("#offres-du-jour").exists()).toBe(true);
  });

  it("préparer puis marquer envoyée : la dernière offre gardée", async () => {
    mockGet(starting(3, { first_steps_offer_id: 7 }));
    let wrapper = await mountView();
    expect(wrapper.find("[data-test=first-steps-action]").attributes("href")).toBe("/candidatures/offres/7/preparer");
    mockGet(starting(4, { first_steps_offer_id: 7 }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=first-steps]").find("h2").text()).toBe("Candidature envoyée");
    expect(wrapper.find("[data-test=first-steps-action]").attributes("href")).toBe("/candidatures/offres/7/preparer?doc=postuler");
  });

  it("pendant les premiers pas, pas de rythme ni de lien vers le bilan", async () => {
    mockGet(starting(2, { rhythm: { target: 5, count: 0, days: [], research_today: true } }));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=orp-month]").text()).not.toContain("Voir le bilan");
    expect(wrapper.find(".rhythm-days").exists()).toBe(false);
  });

  it("masquer : partie tout de suite, enregistrée au bout de 6 secondes", async () => {
    vi.useFakeTimers();
    mockGet(starting(1));
    PUT.mockResolvedValue({ response: { ok: true, status: 204 } });
    const wrapper = await mountView();
    await wrapper.find("[data-test=first-steps-dismiss]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=first-steps]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-sentence]").exists()).toBe(true);
    expect(PUT).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(UNDO_MS);
    expect(PUT).toHaveBeenCalledWith("/api/first-steps", { body: { dismissed: true }, keepalive: false });
    vi.useRealTimers();
  });

  it("tout fait : pas de carte ; la réussite quand le serveur le dit", async () => {
    mockGet(today());
    let wrapper = await mountView();
    expect(wrapper.find("[data-test=first-steps]").exists()).toBe(false);
    PUT.mockResolvedValue({ response: { ok: true } });
    mockGet(today({ first_steps_finished: true }));
    wrapper = await mountView();
    expect(document.body.textContent).toContain("Première candidature notée");
    expect(PUT).toHaveBeenCalledWith("/api/first-steps", { body: { celebrated: true } });
    wrapper.unmount();
  });
});

describe("Aujourd'hui épuré (docs/95)", () => {
  const days = [19, 20, 21, 22, 23, 24, 25].map((d, i) => ({ day: `2026-10-${d}`, research: i < 5, sent: 0, paused: false }));
  const rhythm = (extra: Record<string, unknown> = {}) => ({ target: 3, count: 1, days, research_today: true, ...extra });
  const isoIn = (n: number): string => {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };

  it("la phrase du jour : offres, relances, la semaine ; une seule action", async () => {
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    const sentence = wrapper.find("[data-test=today-sentence]");
    expect(sentence.text().replace(/\s+/g, " ")).toBe("12 offres à examiner, 2 relances et encore 2 candidatures pour tenir ta semaine.");
    expect(sentence.findAll("strong").map((s) => s.text())).toEqual(["12 offres", "2 relances"]);
    const cta = wrapper.find("[data-test=today-cta]");
    expect(cta.text()).toBe("Examiner les offres");
    // Les offres du jour sont dans la carte « À faire » (docs/124 §D).
    expect(cta.attributes("href")).toBe("/aujourdhui#offres-du-jour");
  });

  it("la phrase suit la situation : relances seules, tout à jour, jour sans recherche, pause", async () => {
    mockGet(today({ to_review: 0, rhythm: rhythm({ count: 3 }) }));
    let wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("2 relances.");
    expect(wrapper.find("[data-test=today-cta]").text()).toBe("Relancer");

    mockGet(today({ to_review: 0, to_follow_up: 0, rhythm: rhythm({ count: 3 }) }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("Tout est à jour. Ta semaine est faite.");
    expect(wrapper.find("[data-test=today-cta]").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ research_today: false }) }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toContain("Jour sans recherche");
    expect(wrapper.find("[data-test=rest-day]").exists()).toBe(true);
    expect(wrapper.find("[data-test=today-cta]").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ pause_until: "2026-11-03" }) }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("En pause jusqu'au 3 novembre.");
  });

  it("les bandeaux : ce qui a une date, trois au plus, le rendez-vous ORP d'abord", async () => {
    const soon = new Date(Date.now() + 3 * 3600_000).toISOString();
    mockGet(
      today({
        orp_due_date: isoIn(2),
        orp_meeting_at: soon,
        upcoming_interviews: [{ application_id: 4, company: "Bientôt SA", at: soon }],
        interviews_to_review: [{ application_id: 5, company: "Passé SA", interview_on: "2026-10-15", link: "/candidatures/suivi" }],
        alerts_waiting: 1,
      }),
    );
    const wrapper = await mountView();
    const banners = wrapper.findAll(".today-banner");
    expect(banners).toHaveLength(3);
    expect(banners.map((b) => b.attributes("data-test"))).toEqual(["orp-meeting-soon", "upcoming-interview", "orp-urgent"]);
    expect(wrapper.find("[data-test=upcoming-interview]").text()).toMatch(/Entretien (aujourd'hui|demain) à .* chez Bientôt SA/);
    expect(wrapper.find("[data-test=orp-urgent]").text()).toContain("à remettre dans 2 jours");
  });

  it("rien de daté : pas de bandeau", async () => {
    mockGet(today({ orp_due_month: null, orp_due_date: null }));
    const wrapper = await mountView();
    expect(wrapper.findAll(".today-banner")).toHaveLength(0);
  });

  it("À faire : les meilleures offres, les commencées, puis les relances", async () => {
    const followUps = [
      { application_id: 9, company: "Maquette Médias", job_title: "DevOps", orp_month: "2026-09", sent_at: "2026-09-07", status: "relancee" },
      { application_id: 10, company: "Témoin SA", job_title: "SRE", orp_month: "2026-09", sent_at: "2026-09-14", status: "en_attente" },
    ];
    GET.mockImplementation((path: string, opts?: { params?: { query?: Record<string, unknown> } }) => {
      const query = opts?.params?.query ?? {};
      if (path === "/api/today") return Promise.resolve({ data: today({ to_follow_up: 3, follow_ups: followUps }) });
      if (query.view === "in_progress")
        return Promise.resolve({ data: { items: [{ id: 7, title: "SRE", company: "Beta SA", status: "preparing" }, { id: 8, title: "Envoyée", company: "Gamma", status: "applied" }] } });
      return Promise.resolve({ data: { items: [{ id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne", score: 82, links: [] }] } });
    });
    const wrapper = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 5 } } });
    // Les offres du jour, une à la fois (docs/124 §D).
    const offer = wrapper.find("[data-test=pick-card]");
    expect(offer.text()).toContain("Ingénieur DevOps");
    // Métadonnées en icônes (docs/101) : l'entreprise (immeuble), le lieu (repère).
    expect(offer.find("[data-icon=building]").exists()).toBe(true);
    expect(offer.find("[data-icon=pin]").exists()).toBe(true);
    expect(offer.text()).toContain("Acme SA");
    expect(offer.text()).toContain("Lausanne");
    expect(offer.find("[data-test=pick-open]").attributes("href")).toBe("/candidatures/offres?offre=1");
    expect(offer.find("[data-test=pick-count]").text()).toBe("1 sur 1");
    const preparing = wrapper.find("[data-test=preparing]");
    expect(preparing.text()).toContain("SRE");
    expect(preparing.text()).not.toContain("Envoyée");
    expect(preparing.find("a").attributes("href")).toBe("/candidatures/offres/7/preparer");
    const rows = wrapper.findAll("[data-test=follow-ups] a");
    expect(rows).toHaveLength(2);
    expect(rows[0]!.text()).toContain("sans réponse depuis la relance");
    expect(rows[0]!.attributes("href")).toBe("/candidatures/suivi?mois=2026-09&candidature=9");
    expect(wrapper.text()).toContain("Toutes les relances (3)");
    // Clic direct (docs/57) : pas de « › ».
    expect(wrapper.find("[data-test=best]").text()).not.toContain("›");
  });

  it("Mois ORP : le compte, la barre, ce qu'il reste, la semaine", async () => {
    // Le 1er octobre, personne n'est en retard (docs/123 §2, Q).
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1, 9));
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    vi.useRealTimers();
    const card = wrapper.find("[data-test=orp-month]");
    expect(card.find("h2").text()).toBe("Mois ORP");
    expect(card.find("[data-test=month-count]").text().replace(/\s+/g, " ")).toBe("3 / 20 candidatures");
    expect(card.find("[role=progressbar]").attributes("aria-valuenow")).toBe("3");
    // Un segment par candidature de l'objectif (20 : au-delà de 15, une barre continue).
    expect(card.find(".orp-month-bar.continuous").exists()).toBe(true);
    expect(card.find("[data-test=month-left]").text()).toBe("Dans les temps. Encore 17 d'ici le 31 octobre.");
    expect(card.find("[data-test=orp-face]").classes()).toContain("content");
    expect(card.find("[data-test=rhythm-count]").text()).toBe("1 / 3 candidatures");
    expect(card.text()).toContain("Cette semaine");
    // Plus de tuiles, de graphique ni de jauge : ils sont dans le Bilan.
    expect(wrapper.find("[data-test=stat-review]").exists()).toBe(false);
    expect(wrapper.find("[data-test=week-chart]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-gauge]").exists()).toBe(false);
  });
});

describe("Aujourd'hui, les moments (docs/123 §2)", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    try {
      localStorage.clear();
    } catch {
      // stockage indisponible : rien à nettoyer
    }
  });

  it("S : rien d'urgent, le visage ravi, le mois en une ligne, les offres quand même", async () => {
    mockGet(today({ to_review: 0, to_follow_up: 0, orp_due_month: null, orp_due_date: null }));
    const wrapper = await mountView();
    const calm = wrapper.find("[data-test=today-calm]");
    expect(calm.exists()).toBe(true);
    expect(calm.find(".face-mark").attributes("data-mood")).toBe("ravi");
    expect(calm.text()).toContain("Rien d'urgent aujourd'hui");
    expect(calm.find(".orp-month.compact [data-test=month-count]").text()).toBe("Mois ORP · 3 / 20");
    expect(calm.find("[data-test=today-calm-offers]").attributes("href")).toBe("/candidatures/offres");
    // Pas de phrase du jour ni de carte « À faire » en même temps.
    expect(wrapper.find("[data-test=today-sentence]").exists()).toBe(false);
    expect(wrapper.find("[data-test=best]").exists()).toBe(false);
  });

  it("un jour avec des offres à examiner n'est pas calme", async () => {
    mockGet(today());
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=today-calm]").exists()).toBe(false);
  });

  it("R : l'objectif atteint, une victoire une seule fois par mois", async () => {
    mockGet(today({ month_count: 20, month_target: 20 }));
    const first = await mountView();
    expect(document.body.querySelector("[data-test=goal-moment]")?.textContent).toContain("Objectif du mois atteint");
    expect(document.body.querySelector("[data-test=goal-moment] .face-mark")?.classList.contains("wink")).toBe(true);
    first.unmount();
    document.body.innerHTML = "";
    await mountView();
    expect(document.body.querySelector("[data-test=goal-moment]")).toBeNull();
  });
});
