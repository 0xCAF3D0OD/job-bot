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
afterEach(() => vi.resetAllMocks());

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
function mockApi(orpMonth: () => unknown = () => month(), applications: unknown[] = [application], columns: unknown = undefined): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data: path === "/api/orp" ? orpMonth() : path === "/api/orp-columns" ? columns : applications,
    }),
  );
}

async function mountView(path = "/candidatures") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures", component: ApplicationsView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(ApplicationsView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Candidatures, page réunie", () => {
  it("en-tête commun, à relancer, tous les mois", async () => {
    const old = { ...application, id: 9, company: "Ancienne SA", sent_at: "2026-08-01", orp_month: "2026-08" };
    mockApi(() => month(), [application, old]);
    const { wrapper } = await mountView();
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves à remettre");
    expect(wrapper.find("[data-test=tab-orp]").text()).toContain("1");
    expect(wrapper.find("[data-test=follow-up]").text()).toContain("Ancienne SA");
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(1);
    await wrapper.find("[data-test=all-months]").setValue(true);
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(2);
  });

  it("onglet Journal des recherches", async () => {
    mockApi();
    GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/orp" ? month() : path === "/api/searches" ? { items: [], total: 0 } : [] }));
    const { wrapper } = await mountView("/candidatures?vue=journal");
    expect(wrapper.find("[data-test=month]").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-journal]").classes()).toContain("active");
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
    expect(wrapper.text()).toContain("Aucune candidature");
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
    const { wrapper } = await mountView("/candidatures?vue=orp");
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: undefined } } });
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves à remettre avant le 5 novembre 2026");
    expect(wrapper.findAll("[data-test=orp-row]")).toHaveLength(2);
    expect(wrapper.find("[data-test=incomplete]").text()).toContain("1 ligne(s)");
    expect(wrapper.find("[data-test=csv]").attributes("href")).toBe("/api/orp/2026-10/csv");
    // La version imprimée reprend l'en-tête et laisse le n° AVS à remplir.
    expect(wrapper.find(".orp-sheet").text()).toContain("N° AVS : ____");
    // Le lien de la candidature est dans le PDF, sous le poste.
    expect(wrapper.find(".orp-sheet .orp-url").text()).toBe("https://emploi.exemple.ch/postuler/1");
  });

  it("compléter une ligne ouvre la candidature et l'enregistre", async () => {
    mockApi(() => month(), [{ ...application, id: 2, sent_at: "2026-10-02", status: "refus" }]);
    PUT.mockResolvedValue({ data: { id: 2 } });
    const { wrapper } = await mountView("/candidatures?vue=orp");
    // Chaque ligne se modifie ; « À compléter » ouvre le même formulaire.
    expect(wrapper.findAll("[data-test=edit-row]")).toHaveLength(2);
    await wrapper.find("[data-test=complete]").trigger("click");
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
    const months = [month(), month({ state: "remis", submitted_at: "2026-11-03T09:00:00Z" })];
    mockApi(() => months.shift() ?? month());
    PUT.mockResolvedValue({ response: { status: 204 } });
    DELETE.mockResolvedValue({ response: { status: 204 } });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { wrapper } = await mountView("/candidatures?vue=orp");
    await wrapper.find("[data-test=submit]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp/{month}/submission", { params: { path: { month: "2026-10" } } });
    expect(wrapper.find("[data-test=state]").text()).toContain("Preuves remises le 3 novembre 2026");
    await wrapper.find("[data-test=cancel-submit]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalled();
  });

  it("saisie Job-Room : copie un champ", async () => {
    mockApi();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const { wrapper } = await mountView("/candidatures?vue=orp");
    await wrapper.find("[data-test=job-room]").setValue(true);
    expect(wrapper.findAll("[data-test=job-room-row]")).toHaveLength(2);
    await wrapper.findAll("[data-test=copy]")[1]!.trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("Acme SA");
    expect(wrapper.findAll("[data-test=copy]")[1]!.text()).toBe("Copié");
  });

  it("navigation de mois : passe par l'URL", async () => {
    mockApi();
    const { wrapper, router } = await mountView("/candidatures?vue=orp");
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ vue: "orp", mois: "2026-09" });
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-09" } } });
  });
});


describe("Candidatures, colonnes des preuves", () => {
  it("masque une colonne à l'écran et enregistre le choix", async () => {
    mockApi(() => month(), [], { visible: ["result", "url"] });
    PUT.mockResolvedValue({ data: { visible: ["result"] } });
    const { wrapper } = await mountView("/candidatures?vue=orp");
    const headers = () => wrapper.findAll(".orp-table th").map((th) => th.text());
    expect(headers()).toEqual(["Date", "Entreprise", "Poste", "Résultat", "Lien", "Actions"]);
    // La ligne sans adresse garde son « À compléter » même si la colonne adresse est masquée.
    expect(wrapper.find("[data-test=complete]").exists()).toBe(true);

    await wrapper.find("[data-test=columns]").trigger("click");
    await wrapper.find("[data-test=column-url]").setValue(false);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-columns", { body: { visible: ["result"] } });
    expect(headers()).not.toContain("Lien");
    // Le PDF garde toutes les colonnes.
    expect(wrapper.find(".orp-sheet").text()).toContain("Personne de contact, téléphone");
  });
});
