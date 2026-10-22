import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ApplicationsView from "./ApplicationsView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
// La vue liste par défaut ici : ces tests portent sur la liste et la feuille ORP ;
// le calendrier a ses propres tests (docs/22).
beforeEach(() => localStorage.setItem("jobbot-suivi-vue", "list"));
afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

const row = (id: number, extra: Record<string, unknown> = {}) => ({
  application_id: id,
  date: "02.10.2026",
  company: "Acme SA",
  address: "Avenue de l'Exemple 5, 1003 Lausanne",
  contact: "",
  phone: "",
  job_title: "Ingénieur DevOps junior",
  rate: "plein temps",
  method: "électronique",
  assigned: "non",
  result: "en suspens",
  url: "https://emploi.exemple.ch/postuler/1",
  missing: [],
  declared_at: null,
  job_room: [
    { step: "Quand avez-vous postulé ?", label: "Date", value: "02.10.2026", choice: false },
    { step: "Comment avez-vous postulé ?", label: "Mode", value: "Par voie électronique", choice: true },
    { step: "Auprès de quelle entreprise ?", label: "Entreprise", value: "Acme SA", choice: false },
    { step: "Auprès de quelle entreprise ?", label: "Rue", value: "Avenue de l'Exemple", choice: false },
    { step: "Résultat", label: "Résultat", value: "En suspens", choice: true },
  ],
  ...extra,
});

function month(extra: Record<string, unknown> = {}) {
  return {
    month: "2026-10",
    state: "a_remettre",
    due_date: "2026-11-05",
    count: 2,
    target: 20,
    incomplete: 1,
    to_declare: 2,
    rows: [row(1), row(2, { address: "", missing: ["adresse de l'entreprise"] })],
    submitted_at: null,
    exported_at: null,
    changed_after_submit: false,
    holder: { name: "Camille Exemple", address: "Rue du Test 1, 1020 Renens" },
    searches: [{ received_at: "2026-10-05T07:00:00Z", source: "jobup", label: "DevOps", results_count: 4 }],
    ...extra,
  };
}

const application = {
  id: 3,
  offer_id: 12,
  sent_at: "2026-10-03",
  method: "electronique",
  assigned_by_orp: false,
  company: "Acme SA",
  company_address: null,
  contact_name: null,
  contact_phone: null,
  job_title: "Ingénieur DevOps junior",
  location: "Lausanne",
  rate_text: "plein temps",
  status: "en_attente",
  status_reason: null,
  status_at: null,
  interview_at: "2026-10-20T09:00:00Z",
  orp_month: "2026-10",
  reminded_at: null,
  created_at: "2026-10-03T10:00:00Z",
};

// Page Candidatures réunie (docs/18 §2) : /api/orp donne le mois et l'état, /api/applications la liste.
function mockApi(orpMonth: () => unknown = () => month(), applications: unknown[] = [application]): void {
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/orp" ? orpMonth() : applications }));
}

// Onglets de la rubrique Candidatures (docs/19 §2) : la vue vient de la route.
async function mountView(path = "/candidatures/suivi") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures/suivi", component: ApplicationsView, props: { view: "suivi" } },
      { path: "/candidatures/preuves", component: ApplicationsView, props: { view: "orp" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const view = path.includes("preuves") ? "orp" : "suivi";
  const wrapper = mount(ApplicationsView, {
    props: { view },
    global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } },
  });
  await flushPromises();
  return { wrapper, router };
}

describe("Candidatures, page réunie", () => {
  it("en-tête commun, à relancer, tous les mois", async () => {
    const old = { ...application, id: 9, company: "Ancienne SA", sent_at: "2026-08-01", orp_month: "2026-08" };
    mockApi(() => month(), [application, old]);
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves à remettre");
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(1);
    await wrapper.find("[data-test=all-months]").setValue(true);
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(2);
  });

});

describe("Candidatures, onglet Suivi", () => {
  it("liste les candidatures du mois et le compteur ORP", async () => {
    mockApi(() => month({ count: 1, target: 20 }), [application]);
    const { wrapper } = await mountView();
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(1);
    expect(wrapper.text()).toContain("Acme SA");
    expect(wrapper.find("[data-test=goal]").text()).toContain("1 / 20");
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("5");
  });

  it("sans objectif : invite à le saisir", async () => {
    mockApi(() => month({ count: 0, target: null }), []);
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=goal]").text()).toContain("Réglages");
    // Un compte sans aucune candidature : ce qui remplit le Suivi (docs/128 §3).
    expect(wrapper.text()).toContain("Pas encore de candidature");
    expect(wrapper.find("[data-test=applications-none-yet]").exists()).toBe(true);
  });

  it("changer de mois recharge la liste", async () => {
    mockApi(() => month({ count: 0 }), []);
    const { wrapper } = await mountView();
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/api/applications");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-09" } } });
  });

  it("changer le statut garde la date d'entretien", async () => {
    mockApi(() => month({ count: 1, target: 20 }), [application]);
    PUT.mockResolvedValue({ data: { ...application, status: "entretien" } });
    const { wrapper } = await mountView();
    await wrapper.find("[data-test=status-select]").setValue("entretien");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications/{application_id}");
    expect(opts.body.status).toBe("entretien");
    expect(opts.body.interview_at).toBe(application.interview_at);
  });

  it("ajout manuel : crée une candidature sans offre", async () => {
    mockApi(() => month({ count: 0 }), []);
    POST.mockResolvedValue({ data: application });
    const { wrapper } = await mountView();
    await wrapper.find("[data-test=add-application]").trigger("click");
    const form = wrapper.find("form.application-form");
    expect(form.exists()).toBe(true);
    const inputs = form.findAll("input[type=text]");
    await inputs[0]!.setValue("Beta Sàrl");
    await inputs[1]!.setValue("Platform engineer");
    await form.trigger("submit");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toMatchObject({ offer_id: null, company: "Beta Sàrl", job_title: "Platform engineer" });
    expect(wrapper.find("form.application-form").exists()).toBe(false);
  });
});

describe("Candidatures, onglet Preuves ORP", () => {
  it("affiche le mois, l'état et les lignes à compléter", async () => {
    mockApi();
    const { wrapper } = await mountView("/candidatures/preuves");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: undefined } } });
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves à remettre avant le 5 novembre 2026");
    // PDF et CSV dans le « ⋯ » de la barre du mois (docs/85 §3) ; plus de colonnes à choisir.
    await wrapper.find("[data-test=orp-more]").trigger("click");
    expect(wrapper.find("[data-test=csv]").attributes("href")).toBe("/api/orp/2026-10/csv");
    expect(wrapper.find("[data-test=csv]").attributes("download")).toBe("");
    expect(wrapper.find("[data-test=pdf]").exists()).toBe(true);
    expect(wrapper.find("[data-test=columns]").exists()).toBe(false);
    // La version imprimée reprend l'en-tête et laisse le n° AVS à remplir.
    expect(wrapper.find(".orp-sheet").text()).toContain("N° AVS : ____");
    // Le lien de la candidature est dans le PDF, sous le poste.
    expect(wrapper.find(".orp-sheet .orp-url").text()).toBe("https://emploi.exemple.ch/postuler/1");
  });

  it("À déclarer dans Job-Room : une ligne par candidature, cliquable (docs/85)", async () => {
    localStorage.setItem("jobbot-suivi-vue", "calendar");
    const declared = { ...application, id: 1, company: "Déjà SA" };
    const left = { ...application, id: 2, company: "Reste SA", sent_at: "2026-10-02" };
    const rows = [row(1, { declared_at: "2026-10-12", company: "Déjà SA" }), row(2, { company: "Reste SA", missing: ["adresse de l'entreprise"] })];
    const months = [month({ to_declare: 1, rows }), month({ to_declare: 0, rows: [rows[0], { ...rows[1], declared_at: "2026-10-19" }] })];
    mockApi(() => months.shift() ?? month({ to_declare: 0, rows: [rows[0]] }), [declared, left]);
    PUT.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountView();
    const list = wrapper.find("[data-test=declare]");
    expect(list.text()).toContain("À déclarer dans Job-Room");
    expect(list.findAll("li")).toHaveLength(1);
    const item = list.find("[data-test=declare-2]");
    // La forme de ligne d'Aujourd'hui (docs/130 §A) : l'entreprise, le poste, la date ; « Déclarer ».
    expect(item.text()).toContain("envoyée le 2 octobre");
    expect(item.find("strong").text()).toBe("Reste SA");
    expect(item.text()).toContain("Ingénieur DevOps junior");
    expect(item.find(".today-row-action").text()).toBe("Déclarer");
    expect(list.find("h2").text()).toBe("À déclarer dans Job-Room · 1");
    expect(item.text()).toContain("à compléter");
    // Un clic ouvre le panneau : l'offre, « Modifier », les champs et « Marquer comme déclarée ».
    await item.trigger("click");
    const panel = wrapper.find("[data-test=application-panel]");
    expect(panel.find("[data-test=card-job-room-fields]").exists()).toBe(true);
    await panel.find("[data-test=job-room-mark]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}/job-room", {
      params: { path: { application_id: 2 } },
    });
    expect(wrapper.find("[data-test=declare-done]").text()).toBe("Tout est déclaré.");
    // Le panneau d'un jour choisi n'affiche pas la liste.
    await wrapper.find("[data-test=day-2026-10-02]").trigger("click");
    expect(wrapper.find("[data-test=declare]").exists()).toBe(false);
  });

  it("une action à la fois : compléter tant qu'une ligne manque", async () => {
    // La ligne 2 (sans adresse) correspond à la candidature 2.
    mockApi(() => month(), [{ ...application, id: 2 }]);
    const { wrapper } = await mountView("/candidatures/preuves");
    expect(wrapper.find("[data-test=complete-next]").text()).toContain("Compléter 1 ligne");
    expect(wrapper.find("[data-test=submit]").exists()).toBe(false);
    expect(wrapper.find("[data-test=more-options]").exists()).toBe(false);
    await wrapper.find("[data-test=complete-next]").trigger("click");
    await flushPromises();
    expect(wrapper.find("form.application-form").exists()).toBe(true);
  });

  it("compléter une ligne ouvre la candidature et l'enregistre", async () => {
    mockApi(() => month(), [{ ...application, id: 2, sent_at: "2026-10-02", status: "refus" }]);
    PUT.mockResolvedValue({ data: { id: 2 } });
    const { wrapper } = await mountView("/candidatures/preuves");
    await wrapper.find("[data-test=complete-next]").trigger("click");
    await flushPromises();
    const form = wrapper.find("form.application-form");
    expect(form.exists()).toBe(true);
    await form.findAll("input[type=text]")[2]!.setValue("Rue 1, 1000 Lausanne");
    await form.trigger("submit");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications/{application_id}");
    expect(opts.body.company_address).toBe("Rue 1, 1000 Lausanne");
  });

  it("marquer comme remis puis annuler", async () => {
    // Toutes les lignes complètes : « Marquer comme remis » est l'action proposée.
    const complete = { incomplete: 0, rows: [row(1), row(2)] };
    const months = [month(complete), month({ ...complete, state: "remis", submitted_at: "2026-11-03T09:00:00Z" })];
    mockApi(() => months.shift() ?? month(complete));
    PUT.mockResolvedValue({ response: { status: 204 } });
    DELETE.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountView("/candidatures/preuves");
    await wrapper.find("[data-test=submit]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp/{month}/submission", { params: { path: { month: "2026-10" } } });
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves remises le 3 novembre 2026");
    // La carte qui vient devant (docs/61 §1).
    expect(wrapper.find("[data-test=submitted-moment]").text()).toContain("Preuves d'octobre remises");
    // Annuler la remise se confirme dans la page (docs/108 §1).
    await wrapper.find("[data-test=cancel-submit]").trigger("click");
    expect(DELETE).not.toHaveBeenCalled();
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalled();
  });

  it("navigation de mois : passe par l'URL", async () => {
    mockApi();
    const { wrapper, router } = await mountView("/candidatures/preuves");
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/preuves?mois=2026-09");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-09" } } });
  });
});


describe("Suivi en calendrier (docs/22)", () => {
  // Seule la date est figée, au 10 octobre 2026 : l'entretien du 20 reste à venir,
  // quel que soit le jour où le test tourne. Les minuteries restent réelles.
  afterEach(() => vi.useRealTimers());

  it("pastilles par jour, cartes au clic, à relancer par défaut, copie Job-Room", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-10T08:00:00Z"));
    localStorage.setItem("jobbot-suivi-vue", "calendar");
    const old = { ...application, id: 9, company: "Ancienne SA", sent_at: "2026-08-01", orp_month: "2026-08", interview_at: null };
    const sent = { ...application, id: 2, sent_at: "2026-10-02", interview_at: "2026-10-20T09:00:00Z" };
    mockApi(() => month(), [sent, old]);
    PUT.mockResolvedValue({ data: sent });
    const { wrapper } = await mountView();
    // Sans jour choisi : les candidatures à relancer.
    expect(wrapper.find("[data-test=day-panel]").text()).toContain("À relancer");
    expect(wrapper.find("[data-test=day-panel]").text()).toContain("Ancienne SA");
    // Le 2 octobre : une pastille, avec le point rouge de la ligne ORP à compléter (ligne 2).
    const day = wrapper.find("[data-test=day-2026-10-02]");
    expect(day.findAll(".dot")).toHaveLength(1);
    expect(day.find(".dot").classes()).toContain("incomplete");
    expect(wrapper.find("[data-test=day-2026-10-20] [data-test=mark-interview]").exists()).toBe(true);
    await day.trigger("click");
    const cards = wrapper.findAll("[data-test=day-panel] [data-test=application-card]");
    expect(cards).toHaveLength(1);
    // Carte calme (docs/46) : pastille de statut, une seule prochaine étape (l'entretien à venir).
    expect(cards[0]!.find("[data-test=card-status]").text()).toBe("En attente");
    expect(cards[0]!.find("[data-test=card-step-prepare]").exists()).toBe(true);
    expect(cards[0]!.find("[data-test=card-missing]").exists()).toBe(false);
    // Le panneau : statut, ORP (Job-Room déplié), contacts.
    await cards[0]!.find("[data-test=card-open]").trigger("click");
    const panel = wrapper.find("[data-test=application-panel]");
    expect(panel.find("[data-test=card-missing]").text()).toContain("adresse de l'entreprise");
    expect(panel.find("[data-test=card-job-room-fields]").text()).toContain("Par voie électronique");
    const titles = panel.findAll(".panel-section h3").map((h) => h.text());
    expect(titles).toEqual(["Statut", "Entretiens", "Pour l'ORP", "Contacts"]);
    await panel.find("[data-test=panel-status]").setValue("entretien");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}", expect.objectContaining({ params: { path: { application_id: 2 } } }));
    // Un entretien proposé : une victoire, le visage ravi (docs/123 §2, R).
    const moment = wrapper.find("[data-test=interview-moment]");
    expect(moment.text()).toContain("Un entretien chez");
    expect(moment.find(".face-mark").attributes("data-mood")).toBe("ravi");
    // Calendrier / Liste, retenu.
    await wrapper.find("[data-test=layout-list]").trigger("click");
    expect(localStorage.getItem("jobbot-suivi-vue")).toBe("list");
    expect(wrapper.find("[data-test=calendar]").exists()).toBe(false);
  });

  it("relancée : « Sans réponse » proposé 14 jours après la relance, pas avant", async () => {
    localStorage.setItem("jobbot-suivi-vue", "calendar");
    const ago = (days: number): string => {
      const d = new Date();
      d.setDate(d.getDate() - days);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    };
    const base = { ...application, status: "relancee", sent_at: ago(30), interview_at: null };
    const silent = { ...base, id: 4, company: "Muette SA", followed_up_at: ago(14) };
    const recent = { ...base, id: 5, company: "Récente SA", followed_up_at: ago(13) };
    mockApi(() => month(), [silent, recent]);
    const { wrapper } = await mountView();
    const panel = wrapper.find("[data-test=day-panel]");
    expect(panel.text()).toContain("Muette SA");
    expect(panel.text()).not.toContain("Récente SA");
    expect(panel.find("[data-test=card-step-no-answer]").exists()).toBe(true);
    expect(panel.find("[data-test=card-step-follow-up]").exists()).toBe(false);
    // « Sans réponse › » passe la candidature en Sans réponse.
    PUT.mockResolvedValue({ data: silent });
    await panel.find("[data-test=card-step-no-answer]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith(
      "/api/applications/{application_id}",
      expect.objectContaining({ body: expect.objectContaining({ status: "sans_reponse" }) }),
    );
  });
});

describe("Suivi, une carte et un panneau (docs/46)", () => {
  it("la prochaine étape suit l'ordre : relance, puis ORP, sinon Gérer ; la liste ouvre le panneau", async () => {
    localStorage.setItem("jobbot-suivi-vue", "calendar");
    const ago = (days: number): string => {
      const d = new Date();
      d.setDate(d.getDate() - days);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    };
    const late = { ...application, id: 2, company: "Lente SA", sent_at: ago(12), interview_at: null };
    mockApi(() => month(), [late]);
    const { wrapper } = await mountView();
    const card = wrapper.find("[data-test=day-panel] [data-test=application-card]");
    expect(card.find("[data-test=card-step]").text()).toContain("Sans réponse depuis 10 jours");
    await card.find("[data-test=card-step-follow-up]").trigger("click");
    expect(wrapper.find("[data-test=application-panel]").exists()).toBe(false);
    expect(wrapper.text()).toContain("Relancer Lente SA");

    await wrapper.find("[data-test=layout-list]").trigger("click");
    await wrapper.find("[data-test=table-open]").trigger("click");
    expect(wrapper.find("[data-test=application-panel]").exists()).toBe(true);
    await wrapper.find("[data-test=panel-more]").trigger("click");
    await wrapper.find("[data-test=panel-edit]").trigger("click");
    // Le formulaire prend la place du panneau.
    expect(wrapper.find("[data-test=application-panel]").exists()).toBe(false);
    expect(wrapper.find("form.application-form").exists()).toBe(true);
  });
});

describe("À relancer : des lignes, 5 puis la suite (docs/130 §A)", () => {
  it("cinq lignes, « Voir les 2 autres » déplie le reste ; plus de liste défilante", async () => {
    localStorage.setItem("jobbot-suivi-vue", "calendar");
    const many = [1, 2, 3, 4, 5, 6, 7].map((n) => ({ ...application, id: 20 + n, company: `Exemple ${n}`, sent_at: "2026-08-0" + n }));
    mockApi(() => month(), many);
    const { wrapper } = await mountView();
    const panel = wrapper.find("[data-test=day-panel]");
    expect(panel.find("h2").text()).toBe("À relancer · 7");
    expect(panel.findAll("[data-test=application-card]")).toHaveLength(5);
    expect(wrapper.find("[data-test=panel-scroll]").exists()).toBe(false);
    const more = panel.find("[data-test=panel-show-all]");
    expect(more.text()).toBe("Voir les 2 autres");
    await more.trigger("click");
    expect(panel.findAll("[data-test=application-card]")).toHaveLength(7);
    expect(panel.find("[data-test=panel-show-all]").exists()).toBe(false);
    // Une ligne : l'entreprise, le poste et la date, l'étape ; l'action à droite.
    const first = panel.find("[data-test=application-card]");
    expect(first.find("[data-test=card-step]").text()).toContain("Sans réponse depuis 10 jours");
    expect(first.find("[data-test=card-step-follow-up]").text()).toBe("Relancer");
  });
});

describe("Suivi, revue des pages (docs/43 n° 14)", () => {
  it("ligne 1 : le mois et les outils ; ligne 2 : le compte, et l'état ORP s'il y a à faire (docs/130 §A)", async () => {
    mockApi(() => month());
    const { wrapper } = await mountView();
    const head = wrapper.find(".applications-head");
    expect(head.find("[data-test=month]").exists()).toBe(true);
    expect(head.find(".applications-tools [data-test=layout-calendar]").exists()).toBe(true);
    expect(head.find(".applications-tools [data-test=add-application]").text()).toBe("Ajouter");
    const summary = wrapper.find(".applications-summary");
    expect(summary.find("[data-test=goal]").exists()).toBe(true);
    expect(summary.find(".applications-todo [data-test=state]").text()).toContain("Preuves à remettre");

    mockApi(() => month({ state: "en_cours", incomplete: 0, rows: [row(1)] }));
    const { wrapper: calm } = await mountView();
    expect(calm.find(".applications-todo").exists()).toBe(false);
  });
});
