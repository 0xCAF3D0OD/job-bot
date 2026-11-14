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
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/today" ? day : path === "/api/identity" ? { name: "Kevin Exemple" } : { items: [OFFER] } }));
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
  // L'Accueil du téléphone et le petit livre sont chargés à part.
  await vi.dynamicImportSettled();
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
    expect(wrapper.find("[data-test=orp-bar-week]").exists()).toBe(false);
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

describe("Aujourd’hui sur ordinateur (maquette AujourdhuiOrdinateurV2 du 13 novembre, état « repos » du 14)", () => {
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

  it("l’accroche : « Bonjour », le titre (l’action du jour, sa fin à la main) en un seul titre, la phrase, le personnage", async () => {
    onFirstOfOctober();
    mockGet(today({ rhythm: rhythm(), orp_due_month: null, orp_due_date: null }));
    const wrapper = await mountView();
    const band = wrapper.find("[data-test=today-band]");
    expect(band.find("[data-test=page-eyebrow]").text()).toBe("Bonjour Kevin");
    // Le personnage est décoratif : aucun texte dans l'image.
    expect(band.find("img").attributes("alt")).toBe("");
    // 17 candidatures en 22 jours ouvrables : 1 par jour.
    const title = band.find("h1");
    expect(title.text().replace(/\s+/g, " ")).toBe("1 candidature à envoyer.");
    expect(band.findAll("h1")).toHaveLength(1);
    // Un seul accent manuscrit par écran.
    expect(wrapper.findAll(".aj-title-hand")).toHaveLength(1);
    expect(title.find(".aj-title-hand").text()).toBe("à envoyer.");
    expect(band.find("[data-test=today-sub]").text()).toBe("C’est ton rythme pour rester dans l’objectif ORP. 1 offre est à trier.");
    expect(GET).toHaveBeenCalledWith("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 5 } } });
    // Plus de bande d'action ni de « À retenir » : le tri est une tâche.
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=today-retain]").exists()).toBe(false);
  });

  it("le titre suit la situation : objectif atteint, jour de repos, pause", async () => {
    const nothing = { to_review: 0, to_follow_up: 0, orp_due_month: null, orp_due_date: null };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? today({ ...nothing, month_count: 20, rhythm: rhythm({ count: 3 }) }) : { items: [] } }),
    );
    // « C'est fait ! » déjà vu ce mois-ci sur cet appareil : la page, dans son état « atteint ».
    localStorage.setItem("jobA1.orp-goal.2026-10", "1");
    let wrapper = await mountView();
    // L'objectif du mois atteint (lot du 13 novembre au soir, §6) : en vert, puis la suite en bleu.
    const hands = wrapper.findAll("[data-test=today-sentence] .aj-hand");
    expect(hands.map((h) => h.text())).toEqual(["Objectif du mois atteint,", "la suite est en plus"]);
    expect(hands[0]!.classes()).toContain("aj-hand-reached");
    expect(wrapper.find("[data-test=today-sub]").text()).toMatch(/^Tes 20 recherches d(e |’)\S+ sont faites\. Ce que tu envoies maintenant compte en plus\.$/);
    expect(wrapper.find("[data-test=month-count]").text()).toBe("20 sur 20");
    expect(wrapper.find("[data-test=today-tasks]").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ research_today: false, count: 3 }), orp_due_date: isoIn(2) }));
    wrapper = await mountView();
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Jour de repos.");
    // Le jour de repos suit le gabarit commun (planche AujourdhuiOrdinateurV2, état « repos », 14 novembre) : tout le
    // titre à la main, la liste « Si tu veux avancer », la barre ORP et « 3 sur 3, faite », les offres à trier.
    expect(wrapper.find(".aj").exists()).toBe(true);
    expect(wrapper.find("[data-test=today-sentence] .aj-hand").text()).toBe("Jour de repos.");
    expect(wrapper.find("[data-test=page-eyebrow]").text()).toBe("Bonjour Kevin");
    expect(wrapper.find("[data-test=today-sub]").text()).toBe("Ta semaine est faite. Si tu veux avancer, 2 choses t’attendent.");
    expect(wrapper.find("#today-todo-title").text()).toBe("Si tu veux avancer");
    expect(wrapper.findAll("[data-test=today-tasks] li").map((li) => li.find("a").attributes("data-test"))).toEqual(["orp-urgent", "triage"]);
    expect(wrapper.find("[data-test=today-later] [data-test=follow-ups]").exists()).toBe(true);
    expect(wrapper.find("[data-test=orp-bar-week] span").text()).toBe("3 sur 3, faite");
    expect(wrapper.find(".rhythm-band-days").exists()).toBe(false);

    mockGet(today({ rhythm: rhythm({ pause_until: "2026-11-03" }), orp_due_date: isoIn(-3) }));
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
    expect(section.find("[data-test=orp-urgent] .aj-action").text()).toBe("Remettre");
    // Les tâches sont numérotées ; celle en retard est la première et le dit (PR 49).
    expect(section.element.querySelector("ol")).not.toBeNull();
    expect(section.findAll(".aj-num").map((n) => n.text())).toEqual(["1", "2", "3", "4", "5", "6"]);
    expect(section.find("[data-test=orp-urgent]").text()).toMatch(/En retard depuis le \d/);
    // L'accroche : le retard d'abord, à la main, puis le rythme du jour.
    const hands = wrapper.findAll("[data-test=today-sentence] .aj-hand").map((h) => h.text());
    expect(hands[0]).toBe("1 justificatif en retard,");
    expect(hands[1]).toMatch(/^puis \d+ candidatures?$/);
    expect(wrapper.find("[data-test=today-sub]").text()).toBe("Commence par l’ORP\u202f: 2 minutes. Ensuite, ton rythme du jour.");
    // « Quand tu as le temps » garde son icône, sans numéro.
    expect(wrapper.find("[data-test=today-later] .aj-num").exists()).toBe(false);
    // La carte des justificatifs est en tête du Bilan › ORP (récapitulatif du 11 novembre, PR 29).
    expect(section.find("[data-test=orp-urgent]").attributes("href")).toBe("/bilan");
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

  it("la bande ORP de la colonne de droite : le mois, la semaine, et « Voir le suivi »", async () => {
    onFirstOfOctober();
    mockGet(today({ rhythm: rhythm() }));
    const wrapper = await mountView();
    const card = wrapper.find("[data-test=orp-month]");
    expect(card.find("h2").text()).toBe("ORP");
    expect(card.find("[data-test=orp-month-link]").text()).toBe("Voir le suivi");
    expect(card.find("[data-test=orp-month-link]").attributes("href")).toBe("/bilan/orp");
    expect(card.find("[data-test=month-count]").text()).toBe("3 sur 20");
    expect(card.text()).toContain("Mois ORP · octobre");
    expect(card.find("[data-test=month-left]").text()).toContain("dans les temps");
    // La barre ORP (PR 48) : la semaine tient en une ligne, sans les ronds des jours.
    expect(card.find("[data-test=orp-bar-week]").text()).toBe("Cette semaine1 sur 3");
    expect(card.findAll("a")).toHaveLength(1);
  });
});

describe("Aujourd’hui, les moments (docs/123 §2)", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    clearStorage();
  });

  it("R : l’objectif atteint, l’écran plein « C’est fait ! » une seule fois par mois", async () => {
    const day = today({ month_count: 20, month_target: 20 });
    const orp = { month: "2026-10", count: 20, target: 20, rows: [], holder: { name: "Kevin Exemple" } };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? day : path === "/api/orp" ? orp : path === "/api/identity" ? { name: "Kevin" } : { items: [OFFER] } }),
    );
    const first = await mountView();
    // L'écran plein (ObjectifAtteintOrdinateur, choix de Kevin du 14.11) à la place de l'ancienne carte, sans
    // « Je n'ai pas postulé » ; « Retour à l'accueil » rend la page.
    expect(first.find("[data-test=goal-reached]").text()).toContain("Objectif ORP d’octobre atteint, 20 recherches sur 20.");
    expect(first.find("[data-test=cancel-applied]").exists()).toBe(false);
    expect(first.find(".aj").exists()).toBe(false);
    expect(document.body.querySelector("[data-test=goal-moment]")).toBeNull();
    await first.find("[data-test=goal-home]").trigger("click");
    expect(first.find("[data-test=goal-reached]").exists()).toBe(false);
    expect(first.find(".aj").exists()).toBe(true);
    first.unmount();
    const again = await mountView();
    expect(again.find("[data-test=goal-reached]").exists()).toBe(false);
  });
});
