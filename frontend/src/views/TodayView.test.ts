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

const OFFER = { id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne", score: 82, why: "Kubernetes : dans ton profil.", first_seen_at: "2026-10-14T08:00:00Z", links: [] };

function mockGet(day: unknown): void {
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/today" ? day : { items: [OFFER] } }));
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/aujourdhui/tri", name: "triage", component: { template: "<div />" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  const wrapper = mount(TodayView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

function clearStorage(): void {
  try {
    localStorage.clear();
  } catch {
    // stockage indisponible : rien à nettoyer
  }
}

describe("Les premiers pas (docs/128)", () => {
  it("une seule prochaine action, à la place de la phrase du jour", async () => {
    mockGet(starting(1));
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=first-steps]");
    expect(card.text()).toContain("2 sur 5");
    expect(card.find("h2").text()).toBe("Alertes sur les sites d’emploi");
    expect(card.find("[data-test=first-steps-action]").attributes("href")).toBe("/candidatures/alertes");
    expect(wrapper.find("[data-test=first-step-profile]").classes()).toContain("done");
    expect(wrapper.find("[data-test=first-step-alerts]").classes()).toContain("current");
    expect(wrapper.find("h1").text()).toBe("Commence par les premiers pas.");
    // Le tri, « À faire » et « À retenir » attendent (docs/interface.md n° 17).
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-tasks]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-retain]").exists()).toBe(false);
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
    expect(card.text()).toContain("d’ici un ou deux jours");
    expect(card.find("[data-test=first-steps-add]").attributes("href")).toBe("/candidatures/offres?ajouter=1");
    // Le mois ORP reste.
    expect(wrapper.find("[data-test=orp-month]").exists()).toBe(true);
  });

  it("aucune offre encore : des offres dès maintenant, sans « en retard » (docs/144)", async () => {
    const url = "https://www.google.com/search?q=Comptable+emploi+Sion&udm=8";
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? starting(1, { has_offers: false, search_url: url, month: "2026-11", month_count: 0, month_target: 10, to_review: 0, to_follow_up: 0, follow_ups: [] }) : { items: [] } }),
    );
    const wrapper = await mountView();
    const group = wrapper.find("[data-test=today-start]");
    expect(group.find("h2").text()).toBe("Des offres dès maintenant");
    const google = group.find("[data-test=start-google]");
    expect(google.attributes("href")).toBe(url);
    expect(google.attributes("target")).toBe("_blank");
    expect(google.attributes("rel")).toBe("noopener noreferrer");
    expect(group.find("[data-test=start-add]").attributes("href")).toBe("/ajouter-une-offre");
    expect(group.find("[data-test=start-forward]").attributes("href")).toBe("/candidatures/alertes");
    expect(wrapper.find("[data-test=orp-month]").text()).toContain("Encore 10 d’ici le 5 décembre");
    expect(wrapper.find("[data-test=orp-month]").text()).not.toContain("retard");
  });

  it("alertes prêtes : pas de second « Ajouter », et plus rien dès la première offre", async () => {
    mockGet(starting(2, { has_offers: false, search_url: null }));
    let wrapper = await mountView();
    const group = wrapper.find("[data-test=today-start]");
    expect(group.find("[data-test=start-google]").exists()).toBe(false);
    expect(group.find("[data-test=start-add]").exists()).toBe(false);
    expect(group.find("[data-test=start-forward]").exists()).toBe(true);
    mockGet(starting(2, { has_offers: true, search_url: null }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-start]").exists()).toBe(false);
  });

  it("garder une offre : le bouton ouvre l’écran de tri", async () => {
    mockGet(starting(2));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=first-steps-action]").attributes("href")).toBe("/aujourdhui/tri");
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
    expect(wrapper.find(".rhythm-band").exists()).toBe(false);
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

describe("Aujourd’hui sur ordinateur (maquette du 8 novembre)", () => {
  const days = [19, 20, 21, 22, 23, 24, 25].map((d, i) => ({ day: `2026-10-${d}`, research: i < 5, sent: i === 1 ? 2 : 0, paused: false }));
  const rhythm = (extra: Record<string, unknown> = {}) => ({ target: 3, count: 1, days, research_today: true, ...extra });
  // Le jour de Zurich, comme l'interface : entre 23 h et minuit UTC, le jour du runner a un jour de retard.
  const isoIn = (n: number): string => {
    const d = new Date(`${new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" })}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  };
  // Le jeudi 1er octobre 2026, 9 h : 22 jours ouvrables jusqu'au 30.
  function onFirstOfOctober(): void {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1, 9));
  }
  afterEach(() => {
    vi.useRealTimers();
    clearStorage();
  });

  it("la bande : la date, le titre (l’action du jour, sa fin à la main) en un seul titre, la phrase", async () => {
    onFirstOfOctober();
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    const band = wrapper.find("[data-test=today-band]");
    expect(band.find("[data-test=page-eyebrow]").text()).toMatch(/octobre/);
    // 17 candidatures en 22 jours ouvrables : 1 par jour.
    const title = band.find("h1");
    expect(title.text().replace(/\s+/g, " ")).toBe("1 candidature à envoyer.");
    expect(band.findAll("h1")).toHaveLength(1);
    // Un seul accent manuscrit par écran.
    expect(wrapper.findAll(".today-hand")).toHaveLength(1);
    expect(title.find(".today-hand").text()).toBe("à envoyer.");
    expect(band.find("[data-test=today-sub]").text()).toBe("C’est ton rythme pour rester dans l’objectif ORP. 1 offre est à trier.");
    expect(GET).toHaveBeenCalledWith("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 5 } } });
    // Plus de bande d'action ni de « À retenir » : le tri est une tâche.
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-retain]").exists()).toBe(false);
  });

  it("le titre suit la situation : à jour, jour de repos, pause", async () => {
    const nothing = { to_review: 0, to_follow_up: 0, orp_due_month: null, orp_due_date: null };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today({ ...nothing, month_count: 20, rhythm: rhythm({ count: 3 }) }) : { items: [] } }),
    );
    let wrapper = await mountView();
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Tout est à jour.");
    expect(wrapper.find("[data-test=today-sub]").text()).toContain("Objectif ORP du mois atteint");
    expect(wrapper.find("[data-test=today-tasks]").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ research_today: false, count: 3 }) }));
    wrapper = await mountView();
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Jour de repos.");
    expect(wrapper.find(".today-hand").text()).toBe("repos.");
    expect(wrapper.find("[data-test=today-sub]").text()).toBe("Ta semaine est faite. Si tu veux avancer, 2 choses t’attendent.");
    // Un jour de repos, une seule liste, sans tri.
    expect(wrapper.find("[data-test=triage]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-later]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-tasks] [data-test=follow-ups]").exists()).toBe(true);

    mockGet(today({ rhythm: rhythm({ pause_until: "2026-11-03" }) }));
    wrapper = await mountView();
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("En pause.");
    expect(wrapper.find("[data-test=today-sub]").text()).toBe("Jusqu’au 3 novembre. Pense à l’annoncer à ton conseiller.");
  });

  it("les tâches : en retard, envoyer, trier, préparer un entretien, puis « Quand tu as le temps »", async () => {
    const soon = new Date(Date.now() + 3 * 3600_000).toISOString();
    const followUps = [
      { application_id: 9, company: "Maquette Médias", job_title: "DevOps", orp_month: "2026-09", sent_at: isoIn(-12), status: "relancee" },
      { application_id: 10, company: "Témoin SA", job_title: "SRE", orp_month: "2026-09", sent_at: isoIn(-10), status: "en_attente" },
    ];
    GET.mockImplementation((path: string, opts?: { params?: { query?: Record<string, unknown> } }) => {
      const query = opts?.params?.query ?? {};
      if (path === "/api/today")
        return Promise.resolve({
          data: today({
            to_follow_up: 6,
            follow_ups: followUps,
            orp_due_date: isoIn(-3),
            upcoming_interviews: [{ application_id: 4, company: "Bientôt SA", at: soon }],
            interviews_to_review: [{ application_id: 5, company: "Passé SA", interview_on: "2026-10-15", link: "/candidatures/suivi" }],
            alerts_waiting: 1,
            rhythm: rhythm(),
          }),
        });
      if (query.view === "in_progress")
        return Promise.resolve({
          data: {
            items: [
              { id: 7, title: "SRE", company: "Beta SA", status: "preparing" },
              { id: 8, title: "Ops", company: "Gamma", status: "preparing" },
              { id: 9, title: "Envoyée", company: "Delta", status: "applied" },
            ],
          },
        });
      return Promise.resolve({ data: { items: [{ ...OFFER, score: 90 }] } });
    });
    const wrapper = await mountView();
    const section = wrapper.find("[data-test=today-tasks]");
    expect(section.find("h2").text()).toBe("À faire");
    expect(section.findAll(".today-task").map((r) => r.attributes("data-test"))).toEqual([
      "orp-urgent",
      "preparing",
      "triage",
      "upcoming-interview",
      "interview-to-review",
      "alerts-waiting",
    ]);
    // Les tons : le retard en pêche, l'entretien en vert.
    expect(section.find("[data-test=orp-urgent]").classes()).toContain("tone-late");
    expect(section.find("[data-test=upcoming-interview]").classes()).toContain("tone-interview");
    expect(section.find("[data-test=preparing]").classes()).toContain("tone-normal");
    expect(section.find("[data-test=orp-urgent] strong").text()).toBe("Remettre les justificatifs de septembre");
    expect(section.find("[data-test=orp-urgent] .today-task-action").text()).toBe("Remettre");
    const preparing = section.find("[data-test=preparing]");
    expect(preparing.find("strong").text()).toBe("Préparer 2 candidatures");
    expect(preparing.text()).toContain("2 offres gardées attendent leur lettre");
    expect(preparing.attributes("href")).toBe("/candidatures/offres?statut=in_progress");
    const triage = section.find("[data-test=triage]");
    expect(triage.find("strong").text()).toBe("Trier 1 offre");
    expect(triage.text()).toContain("Dont 1 très proche de ton profil");
    expect(triage.attributes("href")).toBe("/aujourdhui/tri");
    expect(section.find("[data-test=upcoming-interview]").text()).toMatch(/Bientôt SA · (aujourd’hui|demain) à/);
    // Toute la carte est le lien : pas de bouton dedans.
    expect(section.find("button").exists()).toBe(false);
    const later = wrapper.find("[data-test=today-later]");
    expect(later.find("h2").text()).toBe("Quand tu as le temps");
    const follow = later.find("[data-test=follow-ups]");
    expect(follow.find("strong").text()).toBe("Relancer 6 candidatures");
    expect(follow.text()).toContain("La plus ancienne attend depuis 12 jours");
    expect(follow.attributes("href")).toBe("/candidatures/suivi");
  });

  it("une seule offre gardée : la carte ouvre sa préparation", async () => {
    GET.mockImplementation((path: string, opts?: { params?: { query?: Record<string, unknown> } }) => {
      const query = opts?.params?.query ?? {};
      if (path === "/api/today") return Promise.resolve({ data: today({ to_follow_up: 0, follow_ups: [], orp_due_month: null, orp_due_date: null }) });
      if (query.view === "in_progress") return Promise.resolve({ data: { items: [{ id: 7, title: "SRE", company: "Beta SA", status: "preparing" }] } });
      return Promise.resolve({ data: { items: [] } });
    });
    const wrapper = await mountView();
    const row = wrapper.find("[data-test=preparing]");
    expect(row.find("strong").text()).toBe("Préparer 1 candidature");
    expect(row.text()).toContain("Une offre gardée attend sa lettre");
    expect(row.attributes("href")).toBe("/candidatures/offres/7/preparer");
  });

  it("la carte du mois ORP, à cheval sur la bande : le mois, la semaine, et le lien vers le Bilan", async () => {
    onFirstOfOctober();
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=orp-month]");
    expect(card.attributes("href")).toBe("/bilan/orp");
    expect(card.attributes("aria-label")).toBe("Mois ORP : octobre 3 sur 20, cette semaine 1 sur 3. Voir le bilan");
    expect(card.find("[data-test=month-count]").text()).toBe("3 sur 20");
    expect(card.text()).toContain("Mois ORP · octobre");
    expect(card.find("[data-test=month-left]").text()).toContain("dans les temps");
    expect(card.find("[data-test=rhythm-count]").text()).toBe("1 sur 3");
    // Les ronds : un par jour, le nombre envoyé dedans, le week-end en pointillé.
    expect(card.findAll(".rhythm-band-days li")).toHaveLength(7);
    expect(card.findAll(".rhythm-band-days li.rest")).toHaveLength(2);
    expect(card.find(".rhythm-band-days li.sent").text()).toContain("2");
    // Pas de lien dans le lien.
    expect(card.find("a").exists()).toBe(false);
  });
});

describe("Aujourd’hui, les moments (docs/123 §2)", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    clearStorage();
  });

  it("R : l’objectif atteint, une victoire une seule fois par mois", async () => {
    mockGet(today({ month_count: 20, month_target: 20 }));
    const first = await mountView();
    expect(document.body.querySelector("[data-test=goal-moment]")?.textContent).toContain("Objectif du mois atteint");
    // L'illustration de la réussite à la place du visage (planche « Illustrations »).
    expect(document.body.querySelector("[data-test=goal-moment] .illu")).not.toBeNull();
    expect(document.body.querySelector("[data-test=goal-moment] .face-mark")).toBeNull();
    first.unmount();
    document.body.innerHTML = "";
    await mountView();
    expect(document.body.querySelector("[data-test=goal-moment]")).toBeNull();
  });
});
