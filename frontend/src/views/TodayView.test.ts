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

const HIGHLIGHT = { word: "jobs.ch", sentence: "Plus souvent une réponse que les offres de LinkedIn : 3 sur 5, contre 2 sur 10." };
const OFFER = { id: 1, title: "Ingénieur DevOps", company: "Acme SA", location: "Lausanne", score: 82, why: "Kubernetes : dans ton profil.", first_seen_at: "2026-10-14T08:00:00Z", links: [] };

function mockGet(day: unknown, highlight: unknown = HIGHLIGHT): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/today" ? day : path === "/api/insights" ? { highlight } : { items: [OFFER] } }),
  );
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
    expect(card.find("h2").text()).toBe("Alertes sur les sites d'emploi");
    expect(card.find("[data-test=first-steps-action]").attributes("href")).toBe("/candidatures/alertes");
    expect(wrapper.find("[data-test=first-step-profile]").classes()).toContain("done");
    expect(wrapper.find("[data-test=first-step-alerts]").classes()).toContain("current");
    expect(wrapper.find("[data-test=today-sentence]").exists()).toBe(false);
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
    expect(card.text()).toContain("d'ici un ou deux jours");
    expect(card.find("[data-test=first-steps-add]").attributes("href")).toBe("/candidatures/offres?ajouter=1");
    // Le mois ORP reste.
    expect(wrapper.find("[data-test=orp-month]").exists()).toBe(true);
  });

  it("garder une offre : le bouton ouvre l'écran de tri", async () => {
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

describe("Aujourd'hui en une colonne (1.6.51, docs/interface.md n° 17)", () => {
  const days = [19, 20, 21, 22, 23, 24, 25].map((d, i) => ({ day: `2026-10-${d}`, research: i < 5, sent: 0, paused: false }));
  const rhythm = (extra: Record<string, unknown> = {}) => ({ target: 3, count: 1, days, research_today: true, ...extra });
  const isoIn = (n: number): string => {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  afterEach(clearStorage);

  it("la phrase, puis le tri du jour dans la bande d'action, seule action principale", async () => {
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    const sentence = wrapper.find("[data-test=today-sentence]");
    expect(sentence.text().replace(/\s+/g, " ")).toBe("1 offre à trier et 2 relances.");
    expect(sentence.findAll("strong").map((s) => s.text())).toEqual(["1 offre", "2 relances"]);
    expect(GET).toHaveBeenCalledWith("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 5 } } });
    const band = wrapper.find("[data-test=action-band]");
    expect(band.find("h2").text()).toBe("Tri du jour");
    expect(band.text()).toContain("1 offre à trier :");
    // La meilleure offre en aperçu, en Ligne d'offre compacte : le poste, l'entreprise et le lieu, le
    // verdict en mot ; la ligne mène au tri.
    const preview = band.find("[data-test=best]");
    expect(preview.find(".offer-line-title").text()).toBe("Ingénieur DevOps");
    expect(preview.find(".offer-line-title").attributes("href")).toBe("/aujourdhui/tri");
    expect(preview.find(".offer-line-sub").text()).toBe("Acme SA · Lausanne");
    expect(preview.find(".offer-line-word").text()).toBe("Proche");
    const action = band.find("[data-test=action-band-action]");
    expect(action.text()).toBe("Commencer le tri");
    expect(action.attributes("href")).toBe("/aujourdhui/tri");
    // Une seule action principale sur la page ; le tri se fait sur son écran.
    expect(wrapper.findAll(".primary-link")).toHaveLength(1);
    expect(wrapper.find("[data-test=pick-card]").exists()).toBe(false);
  });

  it("le tri fini sur cet appareil : la carte neutre, « Il reste » dans la phrase", async () => {
    localStorage.setItem(`jobA1.tri.${new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" })}`, "1");
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("Il reste 2 relances.");
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=triage-done]").text()).toContain("Tri terminé · À demain");
  });

  it("rien de noté à trier : la carte neutre « Rien à trier »", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today({ rhythm: rhythm() }) : path === "/api/insights" ? { highlight: null } : { items: [] } }),
    );
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("2 relances.");
    expect(wrapper.find("[data-test=triage-done]").text()).toContain("Rien à trier · À demain");
  });

  it("la phrase suit la situation : tout à jour, jour de repos, pause", async () => {
    const nothing = { to_review: 0, to_follow_up: 0, orp_due_month: null, orp_due_date: null };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today({ ...nothing, month_count: 20, rhythm: rhythm({ count: 3 }) }) : { items: [] } }),
    );
    let wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("Tout est à jour. Ta semaine est faite.");
    // Rien à faire : la section est masquée, la conclusion suffit.
    expect(wrapper.find("[data-test=today-tasks]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Rien d'urgent");
    // Le mois en retard : « Ta semaine est faite » se tait (1.6.27).
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today({ ...nothing, month_count: 1, rhythm: rhythm({ count: 3 }) }) : { items: [] } }),
    );
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("Tout est à jour.");

    mockGet(today({ rhythm: rhythm({ research_today: false }) }));
    wrapper = await mountView();
    // Jour de repos (1.6.26) : une seule phrase, qui dit quoi faire ; pas de tri.
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("Jour de repos. Si tu veux avancer : 2 relances en attente.");
    expect(wrapper.find("[data-test=today-sentence] strong").text()).toBe("2 relances");
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=triage-done]").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ pause_until: "2026-11-03" }) }));
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-sentence]").text()).toBe("En pause jusqu'au 3 novembre.");
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
  });

  it("À faire aujourd'hui : des lignes construites pareil, le daté d'abord", async () => {
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
            orp_due_date: isoIn(2),
            orp_meeting_at: soon,
            upcoming_interviews: [{ application_id: 4, company: "Bientôt SA", at: soon }],
            interviews_to_review: [{ application_id: 5, company: "Passé SA", interview_on: "2026-10-15", link: "/candidatures/suivi" }],
            alerts_waiting: 1,
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
      return Promise.resolve({ data: { items: [] } });
    });
    const wrapper = await mountView();
    const section = wrapper.find("[data-test=today-tasks]");
    expect(section.find("h2").text()).toBe("À faire aujourd'hui");
    expect(section.findAll(".today-task").map((r) => r.attributes("data-test"))).toEqual([
      "orp-meeting-soon",
      "upcoming-interview",
      "orp-urgent",
      "follow-ups",
      "preparing",
      "interview-to-review",
      "alerts-waiting",
    ]);
    const follow = section.find("[data-test=follow-ups]");
    expect(follow.find("strong").text()).toBe("Relancer 6 candidatures");
    expect(follow.text()).toContain("La plus ancienne attend depuis 12 jours.");
    expect(follow.find(".today-task-action").text()).toBe("Relancer");
    expect(follow.attributes("href")).toBe("/candidatures/suivi");
    const preparing = section.find("[data-test=preparing]");
    expect(preparing.find("strong").text()).toBe("Préparer 2 candidatures");
    expect(preparing.text()).toContain("2 offres gardées attendent leur lettre.");
    expect(preparing.attributes("href")).toBe("/candidatures/offres?statut=in_progress");
    expect(section.find("[data-test=orp-urgent]").text()).toContain("Remettre les preuves de");
    expect(section.find("[data-test=upcoming-interview]").text()).toMatch(/(Aujourd'hui|Demain) à .* chez Bientôt SA/);
    expect(section.find("[data-test=alerts-waiting] strong").text()).toBe("Vérifier 1 alerte");
    // Clic direct : la ligne entière est le lien, pas de « › ».
    expect(section.text()).not.toContain("›");
  });

  it("une seule offre gardée : la ligne ouvre sa préparation", async () => {
    GET.mockImplementation((path: string, opts?: { params?: { query?: Record<string, unknown> } }) => {
      const query = opts?.params?.query ?? {};
      if (path === "/api/today") return Promise.resolve({ data: today({ to_follow_up: 0, follow_ups: [], orp_due_month: null, orp_due_date: null }) });
      if (query.view === "in_progress") return Promise.resolve({ data: { items: [{ id: 7, title: "SRE", company: "Beta SA", status: "preparing" }] } });
      return Promise.resolve({ data: { items: [] } });
    });
    const wrapper = await mountView();
    const row = wrapper.find("[data-test=preparing]");
    expect(row.find("strong").text()).toBe("Préparer 1 candidature");
    expect(row.text()).toContain("Une offre gardée attend sa lettre.");
    expect(row.attributes("href")).toBe("/candidatures/offres/7/preparer");
  });

  it("Mois ORP : le mois puis la semaine, dans une carte", async () => {
    // Le 1er octobre, personne n'est en retard (docs/123 §2, Q).
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1, 9));
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    vi.useRealTimers();
    expect(wrapper.find("#today-orp-title").text()).toBe("Mois ORP.");
    const card = wrapper.find("[data-test=orp-month]");
    expect(card.find("[data-test=month-count]").text()).toBe("Ce mois · 3 / 20");
    // Sans la tuile du visage : le mois prend la place (1.6.51, choix de Kevin).
    expect(card.find("[data-test=orp-face]").exists()).toBe(false);
    expect(card.find("[role=progressbar]").attributes("aria-valuenow")).toBe("3");
    expect(card.find(".orp-month-bar.continuous").exists()).toBe(true);
    expect(card.find("[data-test=month-left]").text()).toContain("Dans les temps");
    expect(card.find("[data-test=rhythm-count]").text()).toBe("1 / 3 candidatures");
    expect(card.text()).toContain("Cette semaine");
  });

  it("À retenir : le mot en très grand, la phrase, « Voir le Bilan » ; rien sans écart net", async () => {
    mockGet(today());
    let wrapper = await mountView();
    const retain = wrapper.find("[data-test=today-retain]");
    expect(retain.find("h2").text()).toBe("À retenir.");
    expect(retain.find(".today-retain-word").text()).toBe("jobs.ch");
    expect(retain.text()).toContain("Plus souvent une réponse que les offres de LinkedIn");
    expect(retain.find("[data-test=today-retain-link]").attributes("href")).toBe("/bilan");
    mockGet(today(), null);
    wrapper = await mountView();
    expect(wrapper.find("[data-test=today-retain]").exists()).toBe(false);
  });
});

describe("Aujourd'hui, les moments (docs/123 §2)", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    clearStorage();
  });

  it("R : l'objectif atteint, une victoire une seule fois par mois", async () => {
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
