import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
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
afterEach(() => {
  vi.resetAllMocks();
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

// Deux pages sur la même vue (docs/139 étape 8b) : Envoyées et le Suivi ORP, selon la route.
async function mountView(path = "/candidatures/suivi") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures/suivi", name: "applications", component: ApplicationsView },
      { path: "/bilan/orp", name: "orp-month", component: ApplicationsView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(ApplicationsView, {
    global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } },
  });
  await flushPromises();
  return { wrapper, router };
}

describe("Candidatures, onglet Suivi", () => {
  it("changer de mois recharge la liste", async () => {
    mockApi(() => month({ count: 0 }), []);
    const { wrapper } = await mountView("/bilan/orp");
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/api/applications");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-09" } } });
  });

  it("ajout manuel : crée une candidature sans offre", async () => {
    mockApi(() => month({ count: 0 }), []);
    POST.mockResolvedValue({ data: application });
    const { wrapper } = await mountView("/bilan/orp");
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
    const { wrapper } = await mountView("/bilan/orp");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: undefined } } });
    // Un bandeau daté (docs/134) : ce qui reste à faire, et pour quand.
    // La date de phrase (dates.ts) : l'année seulement quand elle diffère.
    expect(wrapper.find("[data-test=state]").text()).toMatch(/^Preuves d'octobre : 1 ligne à compléter, remise avant le 5 novembre( 2026)?\.$/);
    // PDF et CSV dans le « ⋯ » de la barre du mois (docs/85 §3) ; plus de colonnes à choisir.
    await wrapper.find("[data-test=orp-more]").trigger("click");
    expect(wrapper.find("[data-test=csv]").attributes("href")).toBe("/api/orp/2026-10/csv");
    expect(wrapper.find("[data-test=csv]").attributes("download")).toBe("");
    // Le PDF est le bouton « Exporter le formulaire (PDF) » de la maquette Orp.
    expect(wrapper.find("[data-test=pdf]").text()).toBe("Exporter le formulaire (PDF)");
    expect(wrapper.find("[data-test=columns]").exists()).toBe(false);
    // La version imprimée reprend l'en-tête et laisse le n° AVS à remplir.
    expect(wrapper.find(".orp-sheet").text()).toContain("N° AVS : ____");
    // Le lien de la candidature est dans le PDF, sous le poste.
    expect(wrapper.find(".orp-sheet .orp-url").text()).toBe("https://emploi.exemple.ch/postuler/1");
  });

  it("À déclarer dans Job-Room : une ligne par candidature, cliquable (docs/85)", async () => {
    const declared = { ...application, id: 1, company: "Déjà SA" };
    const left = { ...application, id: 2, company: "Reste SA", sent_at: "2026-10-02" };
    const rows = [row(1, { declared_at: "2026-10-12", company: "Déjà SA" }), row(2, { company: "Reste SA", missing: ["adresse de l'entreprise"] })];
    const months = [month({ to_declare: 1, rows }), month({ to_declare: 0, rows: [rows[0], { ...rows[1], declared_at: "2026-10-19" }] })];
    mockApi(() => months.shift() ?? month({ to_declare: 0, rows: [rows[0]] }), [declared, left]);
    PUT.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountView("/bilan/orp");
    // Sa propre liste, sous les recherches du mois (B8).
    const list = wrapper.find("[data-test=declare]");
    expect(list.attributes("aria-label")).toBe("À déclarer dans Job-Room");
    expect(list.findAll("li")).toHaveLength(1);
    const item = list.find("[data-test=offer-line]");
    // La Ligne d'offre compacte (planche « Ligne d'offre ») : le poste, l'entreprise, l'état ; « Déclarer ».
    expect(item.find(".offer-line-title").text()).toBe("Ingénieur DevOps junior");
    expect(item.find(".offer-line-sub").text()).toContain("Reste SA");
    expect(item.find("[data-test=offer-line-state]").text()).toContain("Envoyée le 2 octobre");
    expect(item.find("[data-test=declare-2]").text()).toBe("Déclarer");
    expect(list.find("h2").text()).toBe("À déclarer · 1");
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
    // Un jour choisi s'affiche sous le calendrier ; « À faire » reste en haut.
    await wrapper.find("[data-test=day-2026-10-02]").trigger("click");
    expect(wrapper.find("[data-test=detail-calendar] [data-test=day-panel]").exists()).toBe(true);
    expect(wrapper.find("[data-test=declare]").exists()).toBe(true);
  });

  it("une action à la fois : compléter tant qu'une ligne manque", async () => {
    // La ligne 2 (sans adresse) correspond à la candidature 2.
    mockApi(() => month(), [{ ...application, id: 2 }]);
    const { wrapper } = await mountView("/bilan/orp");
    expect(wrapper.find("[data-test=complete-next]").text()).toBe("Compléter");
    expect(wrapper.find("[data-test=submit]").exists()).toBe(false);
    expect(wrapper.find("[data-test=more-options]").exists()).toBe(false);
    await wrapper.find("[data-test=complete-next]").trigger("click");
    await flushPromises();
    expect(wrapper.find("form.application-form").exists()).toBe(true);
  });

  it("compléter une ligne ouvre la candidature et l'enregistre", async () => {
    mockApi(() => month(), [{ ...application, id: 2, sent_at: "2026-10-02", status: "refus" }]);
    PUT.mockResolvedValue({ data: { id: 2 } });
    const { wrapper } = await mountView("/bilan/orp");
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
    const { wrapper } = await mountView("/bilan/orp");
    await wrapper.find("[data-test=submit]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp/{month}/submission", { params: { path: { month: "2026-10" } } });
    expect(wrapper.find("[data-test=state]").text()).toMatch(/Preuves d'octobre remises le 3 novembre( 2026)?\./);
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
    const { wrapper, router } = await mountView("/bilan/orp");
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/bilan/orp?mois=2026-09");
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
    const old = { ...application, id: 9, company: "Ancienne SA", sent_at: "2026-08-01", orp_month: "2026-08", interview_at: null };
    const sent = { ...application, id: 2, sent_at: "2026-10-02", interview_at: "2026-10-20T09:00:00Z" };
    mockApi(() => month(), [sent, old]);
    PUT.mockResolvedValue({ data: sent });
    const { wrapper } = await mountView("/bilan/orp");
    expect(wrapper.find("[data-test=todo]").exists()).toBe(false);
    expect(wrapper.find("[data-test=detail-calendar] .disclosure-row").attributes("aria-expanded")).toBe("false");
    expect(wrapper.find("[data-test=day-panel]").exists()).toBe(false);
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
    await cards[0]!.find("[data-test=offer-line-open]").trigger("click");
    const panel = wrapper.find("[data-test=application-panel]");
    expect(panel.find("[data-test=card-missing]").text()).toContain("adresse de l'entreprise");
    expect(panel.find("[data-test=card-job-room-fields]").text()).toContain("Par voie électronique");
    const titles = panel.findAll(".panel-section h3").map((h) => h.text());
    expect(titles).toEqual(["Statut", "Entretiens", "Pour l'ORP", "Contacts"]);
    await panel.find("[data-test=panel-status]").setValue("entretien");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}", expect.objectContaining({ params: { path: { application_id: 2 } } }));
    // Un entretien proposé : « Entretien décroché », en écran plein, le personnage qui fête (docs/141, 12).
    const moment = wrapper.find("[data-test=interview-moment]");
    expect(moment.find("h1").text()).toMatch(/^Entretien décroché chez .+\.$/);
    expect(moment.find("[data-pose=celebration]").exists()).toBe(true);
    expect(moment.find("[role=status]").exists()).toBe(true);
    expect(wrapper.find(".jobs-body").exists()).toBe(false);
    // « Préparer l'entretien » ouvre la préparation de cette candidature.
    GET.mockResolvedValue({ data: null });
    await moment.find("[data-test=interview-prepare]").trigger("click");
    expect(wrapper.find("[data-test=interview-moment]").exists()).toBe(false);
    expect(wrapper.findComponent({ name: "InterviewPreparation" }).props("application")).toMatchObject({ id: 2 });
  });

  it("un refus : une réponse qui encourage et propose la suite, jamais triste (docs/141, 13)", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-10T08:00:00Z"));
    const waiting = { ...application, id: 2, sent_at: "2026-10-02", status: "en_attente" };
    mockApi(() => month(), [waiting]);
    PUT.mockResolvedValue({ data: waiting });
    const { wrapper } = await mountView("/bilan/orp");
    await wrapper.find("[data-test=day-2026-10-02]").trigger("click");
    await wrapper.find("[data-test=day-panel] [data-test=application-card] [data-test=offer-line-open]").trigger("click");
    await wrapper.find("[data-test=application-panel] [data-test=panel-status]").setValue("refus");
    await flushPromises();
    const moment = wrapper.find("[data-test=refusal-moment]");
    expect(moment.find("h1").text()).toMatch(/^Réponse de .+\.$/);
    expect(moment.find("[data-pose=bonjour]").exists()).toBe(true);
    expect(wrapper.find("[data-test=application-panel]").exists()).toBe(false);
    expect(moment.find("[data-test=refusal-next]").attributes("href")).toBe("/candidatures/offres");
    expect(moment.find(".face-mark").exists()).toBe(false);
    await moment.find("[data-test=refusal-close]").trigger("click");
    expect(wrapper.find("[data-test=refusal-moment]").exists()).toBe(false);
    expect(wrapper.find(".jobs-body").exists()).toBe(true);
  });

});

describe("Suivi, l'essentiel d'abord (1.6.20, annexe de l'audit : Suivi trop chargé)", () => {
  it("à déclarer : dans le Suivi ORP seulement, sans « Afficher plus » sous trois lignes", async () => {
    const many = [1, 2, 3, 4, 5, 6, 7].map((n) => ({ ...application, id: 20 + n, company: `Exemple ${n}`, sent_at: "2026-08-0" + n }));
    mockApi(() => month(), many);
    // La liste à déclarer est dans le Suivi ORP, avec ses deux lignes (moins de trois : pas de « Afficher plus »).
    expect((await mountView()).wrapper.find("[data-test=declare]").exists()).toBe(false);
    const declare = (await mountView("/bilan/orp")).wrapper.find("[data-test=declare]");
    expect(declare.findAll("li")).toHaveLength(2);
    expect(declare.find("[data-test=declare-all]").exists()).toBe(false);
  });

  it("le Suivi ORP : retour, mois, objectif, bandeau, export, recherches, puis Ajouter, À déclarer, calendrier (B8)", async () => {
    mockApi(() => month({ count: 6, target: 10 }), [application]);
    const { wrapper } = await mountView("/bilan/orp");
    expect(wrapper.find("h1").text()).toBe("Suivi ORP");
    expect(wrapper.find("[data-test=orp-back]").attributes("href")).toBe("/bilan");
    expect(wrapper.find("[data-test=orp-goal] h2").text()).toBe("4 recherches à faire");
    expect(wrapper.find("#orp-month-title").findAll("span").map((x) => x.text())).toEqual(["Recherches du mois", "2 entrées"]);
    const html = wrapper.html();
    const order = ["data-test=\"month\"", "data-test=\"orp-goal\"", "data-test=\"orp-banner\"", "data-test=\"pdf\"", "data-test=\"orp-rows\"", "data-test=\"add-application\"", "data-test=\"declare\"", "data-test=\"detail-calendar\""].map((t) => html.indexOf(t));
    expect(order.every((at) => at >= 0)).toBe(true);
    expect(order).toEqual([...order].sort((x, y) => x - y));
    // Une recherche ouvre sa candidature.
    mockApi(() => month({ rows: [row(3)] }), [application]);
    const { wrapper: one } = await mountView("/bilan/orp");
    await one.find("[data-test=orp-row-3]").trigger("click");
    expect(one.find("[data-test=application-panel]").exists()).toBe(true);
  });

  it("sur téléphone, le Suivi ORP sans calendrier ; Ajouter et À déclarer restent (décision de Kevin, 6.11)", async () => {
    mockApi(() => month({ count: 6, target: 10 }), [application]);
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    const { wrapper } = await mountView("/bilan/orp");
    vi.unstubAllGlobals();
    expect(wrapper.find("[data-test=suivi-detail]").exists()).toBe(false);
    expect(wrapper.find("[data-test=add-application]").exists()).toBe(true);
    expect(wrapper.find("[data-test=declare]").exists()).toBe(true);
  });

  it("le calendrier replié dans le Suivi ORP, pas dans Envoyées ; un jour demandé l'ouvre", async () => {
    mockApi(() => month(), [{ ...application, sent_at: "2026-10-02" }]);
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=suivi-detail]").exists()).toBe(false);
    const orpPage = (await mountView("/bilan/orp")).wrapper;
    expect(orpPage.find("[data-test=detail-calendar] [data-test=disclosure-description]").text()).not.toBe("");
    expect(wrapper.find("[data-test=layout-calendar]").exists()).toBe(false);

    const { wrapper: day } = await mountView("/bilan/orp?jour=2026-10-02");
    expect(day.find("[data-test=detail-calendar] .disclosure-row").attributes("aria-expanded")).toBe("true");
    expect(day.find("[data-test=day-panel]").text()).toContain("Acme SA");
  });
});

describe("Suivi ORP, le bandeau des preuves (docs/134)", () => {
  it("sous l'objectif, seulement s'il y a à faire ou si elles sont remises", async () => {
    mockApi(() => month());
    const { wrapper } = await mountView("/bilan/orp");
    expect(wrapper.find("[data-test=orp-banner]").classes()).toContain("today-banner");

    mockApi(() => month({ state: "en_cours", incomplete: 0, rows: [row(1)] }));
    const { wrapper: calm } = await mountView("/bilan/orp");
    expect(calm.find("[data-test=orp-banner]").exists()).toBe(false);
  });
});


describe("Envoyées (maquette Envoyees, 7.11.2026)", () => {
  afterEach(() => vi.useRealTimers());
  const at = (sent_at: string, extra: Record<string, unknown> = {}) => ({ ...application, sent_at, interview_at: null, ...extra });

  it("l'objectif ORP et sa barre, vers le Suivi ORP", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-07T08:00:00Z"));
    mockApi(() => month({ month: "2026-11", count: 6, target: 10 }), [at("2026-11-06")]);
    const { wrapper } = await mountView();
    const goal = wrapper.find("[data-test=goal]");
    expect(goal.attributes("href")).toBe("/bilan/orp");
    expect(goal.text()).toContain("Objectif ORP de novembre");
    expect(goal.find("[data-test=goal-count]").text()).toBe("6 sur 10");
    const bar = goal.find("[role=progressbar]");
    expect([bar.attributes("aria-valuenow"), bar.attributes("aria-valuemax")]).toEqual(["6", "10"]);
    expect(bar.find("span").attributes("style")).toContain("width: 60%");
    expect(goal.text()).toContain("Encore 4 d’ici le 30 novembre");
    // Plus de phrase des relances ni de liste repliée (maquette).
    expect(wrapper.find("[data-test=suivi-sentence]").exists()).toBe(false);
    expect(wrapper.find("[data-test=suivi-detail]").exists()).toBe(false);
  });

  it("sans objectif : l'invite à l'indiquer ; sans candidature : ce qui remplit la page", async () => {
    mockApi(() => month({ count: 0, target: null }), []);
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=goal-count]").text()).toBe("À indiquer");
    expect(wrapper.find("[data-test=goal]").attributes("href")).toBe("/reglages?rubrique=recherche");
    expect(wrapper.find("[role=progressbar]").exists()).toBe(false);
    expect(wrapper.find("[data-test=applications-none-yet]").exists()).toBe(true);
  });

  it("les rubriques : à relancer, entretiens, cette semaine, plus tôt ; la carte commune et son statut", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-07T08:00:00Z"));
    const list = [
      at("2026-10-26", { id: 1, company: "Muette SA" }),
      at("2026-10-28", { id: 2, company: "Alpstack", status: "entretien", interview_at: "2026-11-12T13:00:00Z" }),
      at("2026-11-02", { id: 3, company: "Infomaniak", application_url: null }),
      at("2026-11-03", { id: 4, company: "Romandie", application_url: "https://exemple.ch/postuler" }),
      at("2026-10-21", { id: 5, company: "EPFL", status: "refus" }),
      at("2026-11-05", { id: 6, company: "Récente SA", status: "relancee", followed_up_at: "2026-11-06" }),
    ];
    mockApi(() => month({ month: "2026-11" }), list);
    const { wrapper } = await mountView();
    const titles = wrapper.findAll(".offer-day").map((d) => d.text());
    expect(titles).toEqual(["À relancer1 candidature", "Entretiens1 candidature", "Cette semaine3 candidatures", "Plus tôt1 candidature"]);
    const cards = wrapper.findAll("[data-test=application]");
    const read = (i: number) => [
      cards[i]!.find("[data-test=list-card-title]").exists(),
      cards[i]!.findAll("[data-test=sent-chip]").map((c) => c.text()),
      cards[i]!.find("[data-test=sent-status]").text(),
    ];
    expect(read(0)).toEqual([true, ["Envoyée il y a 12 jours"], "Sans réponse"]);
    expect(read(1)).toEqual([true, ["Jeudi 12 nov., 14 h"], "Entretien"]);
    expect(cards[1]!.find("[data-test=sent-chip]").classes()).toContain("green");
    // Cette semaine, la plus récente d'abord, avec le canal.
    expect(read(2)).toEqual([true, ["Envoyée jeudi", "Par e-mail"], "Relancée"]);
    expect(read(3)).toEqual([true, ["Envoyée mardi", "Formulaire en ligne"], "Envoyée"]);
    expect(read(4)).toEqual([true, ["Envoyée lundi", "Par e-mail"], "Envoyée"]);
    expect(read(5)).toEqual([true, ["Envoyée le 21 oct."], "Refusée"]);
    // Rien d'autre dans la carte : ni action, ni « ⋯ ».
    expect(cards[0]!.findAll("button")).toHaveLength(0);
  });

  it("une carte ouvre le panneau de la candidature et se marque", async () => {
    mockApi(() => month(), [at("2026-10-02", { company: "Lente SA" })]);
    const { wrapper } = await mountView();
    const card = wrapper.find("[data-test=application]");
    expect(card.attributes("href")).toBe("/candidatures/suivi?candidature=3");
    await card.trigger("click", { button: 0 });
    expect(wrapper.find("[data-test=application-panel]").exists()).toBe(true);
    expect(wrapper.find("[data-test=application]").attributes("aria-current")).toBe("true");
  });

  it("?q= (recherche globale) : seulement ce qui correspond, sans accents ni casse ; « Tout afficher »", async () => {
    const others = [
      at("2026-09-10", { id: 11, company: "Témoin Industrie SA", job_title: "Ingénieur DevOps" }),
      at("2026-09-11", { id: 12, company: "Banque Exemple", job_title: "Comptable" }),
    ];
    mockApi(undefined, others);
    const { wrapper, router } = await mountView("/candidatures/suivi?q=temoin%20INGENIEUR");
    expect(wrapper.find("[data-test=sent-words]").text()).toContain("Candidatures « temoin INGENIEUR »");
    expect(wrapper.find("[data-test=sent-list]").text()).toContain("Témoin Industrie SA");
    expect(wrapper.find("[data-test=sent-list]").text()).not.toContain("Banque Exemple");
    await wrapper.find("[data-test=sent-words-clear]").trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 350));
    await flushPromises();
    expect(router.currentRoute.value.query.q).toBeUndefined();
    expect(wrapper.find("[data-test=sent-list]").text()).toContain("Banque Exemple");

    const { wrapper: none } = await mountView("/candidatures/suivi?q=boulanger");
    expect(none.find("[data-test=sent-words]").text()).toContain("Aucune candidature pour « boulanger ».");
  });
});
