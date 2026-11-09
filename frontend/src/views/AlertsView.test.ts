import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AlertsView from "./AlertsView.vue";

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
    PATCH: vi.fn(),
  },
}));
afterEach(() => vi.resetAllMocks());

const DAY = 86_400_000;
const cell = (site: string, extra: Record<string, unknown> = {}) => ({
  site,
  url: `https://${site}.example/?term=DevOps`,
  status: "todo",
  received_at: null,
  created_at: null,
  ...extra,
});
const search = (id: number, cells: unknown[], extra: Record<string, unknown> = {}) => ({
  id,
  terms: id === 1 ? "DevOps" : "Kubernetes",
  location: "Lausanne",
  active: true,
  cells,
  ...extra,
});
function page(searches: unknown[]) {
  return {
    mailbox: "moi@exemple.ch",
    folder: "job-bot",
    sites: [
      { slug: "jobup", name: "jobup", senders: ["info@jobup.ch"], prefilled: true },
      { slug: "linkedin", name: "LinkedIn", senders: ["jobs-noreply@linkedin.com"], prefilled: true },
    ],
    searches,
  };
}

async function mountView(data: unknown) {
  GET.mockResolvedValue({ data });
  const wrapper = mount(AlertsView, { global: { stubs: { teleport: true } } });
  await flushPromises();
  return wrapper;
}

describe("Alertes, assistant (docs/21 §4)", () => {
  it("rien en place : assistant en trois étapes, un site à la fois", async () => {
    const todo = page([search(1, [cell("jobup"), cell("linkedin")]), search(2, [cell("jobup"), cell("linkedin")])]);
    PUT.mockResolvedValue({ data: todo });
    DELETE.mockResolvedValue({ data: page([search(1, [cell("jobup"), cell("linkedin")])]) });
    const wrapper = await mountView(todo);
    expect(wrapper.find("[data-test=alerts-wizard]").exists()).toBe(true);
    // La liste vide : le logo transformé « cloche », jamais le personnage (docs/141 §3).
    expect(wrapper.find("[data-test=alerts-empty] [data-transform=alerts]").exists()).toBe(true);
    expect(wrapper.find("[data-illustration=personnage]").exists()).toBe(false);

    // Étape 1 : retirer une recherche.
    expect(wrapper.findAll("[data-test=wizard-search]")).toHaveLength(2);
    await wrapper.findAll("[data-test=wizard-search] button")[1]!.trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=wizard-search]")).toHaveLength(1);
    // L'exemple suit la recherche, pas un métier au hasard (docs/104 §5).
    expect(wrapper.find("[data-test=wizard-terms]").attributes("placeholder")).toBe("Mots (DevOps)");
    await wrapper.find("[data-test=wizard-next]").trigger("click");

    // Étape 2 : jobup, puis LinkedIn ; l'avancée sur la ligne de l'étape, deux boutons (docs/104 §4).
    expect(wrapper.text()).toContain("Crée l'alerte sur jobup");
    expect(wrapper.find("[data-test=wizard-site-count]").text()).toBe("· site 1 sur 2");
    expect(wrapper.find("[data-test=wizard-site-done]").text()).toBe("J'ai créé l'alerte");
    expect(wrapper.find("[data-test=wizard-skip]").text()).toBe("Plus tard");
    expect(wrapper.find("[data-test=wizard-skip]").classes()).toContain("secondary");
    expect(wrapper.find("[data-test=wizard-open]").attributes("href")).toBe("https://jobup.example/?term=DevOps");
    await wrapper.find("[data-test=wizard-site-done]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/alert-searches/{search_id}/sites/{site}", {
      params: { path: { search_id: 1, site: "jobup" } },
    });
    expect(wrapper.text()).toContain("Crée l'alerte sur LinkedIn");
    await wrapper.find("[data-test=wizard-skip]").trigger("click");

    // Étape 3.
    expect(wrapper.text()).toContain("C'est prêt");
    expect(wrapper.text()).toContain("moi@exemple.ch");
  });
});

describe("Alertes, assistant : le bouton bleu ajoute aussi (2026-11-05)", () => {
  it("une recherche tapée sans le « + » est ajoutée par « Continuer », puis l'étape suivante s'ouvre", async () => {
    const wrapper = await mountView(page([]));
    POST.mockResolvedValue({ data: page([search(1, [cell("jobup"), cell("linkedin")])]) });
    await wrapper.find("[data-test=wizard-next]").trigger("click");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("Ajoute au moins une recherche pour continuer.");

    await wrapper.find("[data-test=wizard-terms]").setValue("DevOps");
    await wrapper.find("[data-test=wizard-next]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "DevOps", location: null } });
    expect(wrapper.text()).toContain("Crée l'alerte sur jobup");
  });
});

describe("Alertes, la page (AlertesOrdinateur du 9 novembre, §2.8)", () => {
  it("la phrase, les familles, une carte par alerte avec le mot d'état ; pas de bandeau", async () => {
    const wrapper = await mountView(
      page([
        search(1, [cell("jobup", { status: "received", received_at: new Date(Date.now() - 2 * DAY).toISOString() }), cell("linkedin")]),
        search(2, [cell("jobup"), cell("linkedin", { status: "created", created_at: new Date(Date.now() - 4 * DAY).toISOString() })]),
      ]),
    );
    expect(wrapper.find("[data-test=alerts-wizard]").exists()).toBe(false);
    expect(wrapper.find("h1").text()).toBe("Mes alertes e-mail");
    expect(wrapper.find("[data-test=alerts-sentence]").text()).toMatch(/^2 recherches suivies\. Dernière alerte reçue le /);
    // Plus de bandeau sur ordinateur (§2.8) : l'alerte muette se lit sur sa carte.
    expect(wrapper.find("[data-test=alerts-banner]").exists()).toBe(false);
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    // Les familles : Actives puis À créer, le nombre dans le titre.
    expect(wrapper.findAll(".alerts-family-title").map((h) => h.text())).toEqual(["Actives · 2", "À créer · 2"]);
    const devops = wrapper.find("[data-test=alert-card-1-jobup]");
    expect(devops.find(".block-row-title").text()).toBe("DevOps");
    expect(devops.text()).toContain("Lausanne · jobup");
    expect(devops.find(".block-row-aside").text().replace(/^, /, "")).toMatch(/^Reçue le /);
    const silent = wrapper.find("[data-test=alert-card-2-linkedin] .block-row-aside");
    expect(silent.text().replace(/^, /, "")).toBe("Rien reçu depuis la création");
    expect(silent.classes()).toContain("todo");
    const todo = wrapper.find("[data-test=alert-card-1-linkedin] .block-row-aside");
    expect(todo.text().replace(/^, /, "")).toBe("Pas encore créée");
    expect(todo.classes()).toContain("muted");
    // La carte « À créer » ouvre le panneau ; « Créer l'alerte » ouvre le pas à pas sur ce site, pour cette recherche.
    await wrapper.find("[data-test=alert-card-1-linkedin]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alert-sheet]").text()).toContain("À créer sur LinkedIn");
    await wrapper.find("[data-test=alert-create]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Crée l'alerte sur LinkedIn");
    expect(wrapper.findAll("[data-test=wizard-open]").map((a) => a.text())).toEqual([expect.stringContaining("DevOps")]);
    await wrapper.find("[data-test=close-wizard]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alert-card-1-jobup]").exists()).toBe(true);
  });

  it("une alerte active : le panneau avec les actions ; « + Ajouter » ajoute une recherche", async () => {
    const one = page([search(1, [cell("jobup", { status: "received", received_at: new Date(Date.now() - DAY).toISOString() })])]);
    POST.mockResolvedValue({ data: page([...one.searches, search(2, [cell("jobup")])]) });
    const wrapper = await mountView(one);
    expect(wrapper.find("[data-test=alerts-note]").exists()).toBe(false);
    await wrapper.find("[data-test=alert-card-1-jobup]").trigger("click");
    const sheet = wrapper.find("[data-test=alert-sheet]");
    expect(sheet.text()).toContain("Active · reçue");
    expect(sheet.find("[data-test=alert-offers]").exists()).toBe(true);
    expect(sheet.find("[data-test=alert-remove]").text()).toBe("Ne plus suivre cette recherche");
    await wrapper.find("[data-test=add-search]").trigger("click");
    await wrapper.find("[data-test=add-search-terms]").setValue("Kubernetes");
    await wrapper.find("[data-test=add-search-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "Kubernetes", location: null } });
    expect(wrapper.find("[data-test=alert-card-2-jobup]").exists()).toBe(true);
  });

  it("ajout sans mot : l'erreur sous le champ, le curseur dedans, « (facultatif) » sur le lieu", async () => {
    GET.mockResolvedValue({ data: page([search(1, [cell("jobup", { status: "received", received_at: new Date(Date.now() - DAY).toISOString() })])]) });
    const wrapper = mount(AlertsView, { global: { stubs: { teleport: true } }, attachTo: document.body });
    await flushPromises();
    await wrapper.find("[data-test=add-search]").trigger("click");
    expect(wrapper.find("[data-test=add-search-location]").element.closest(".form-field")?.textContent).toContain("Le lieu (facultatif)");
    await wrapper.find("[data-test=add-search-form]").trigger("submit");
    await flushPromises();
    const terms = wrapper.find("[data-test=add-search-terms]");
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Indique au moins un mot.");
    expect(terms.attributes("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(terms.element);
    expect(POST).not.toHaveBeenCalled();
    await terms.setValue("Kubernetes");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("sans alerte reçue : la phrase le dit", async () => {
    const day = new Date(Date.now() - DAY).toISOString();
    const wrapper = await mountView(page([search(1, [cell("jobup", { status: "created", created_at: day })])]));
    expect(wrapper.find("[data-test=alerts-sentence]").text()).toBe("1 recherche suivie. Aucune alerte reçue pour l'instant.");
    expect(wrapper.find("[data-test=alert-card-1-jobup] .block-row-aside").text().replace(/^, /, "")).toBe("En attente du premier envoi");
  });

  it("des blocs de chargement tant que la page charge (règles §6)", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    const wrapper = mount(AlertsView);
    await flushPromises();
    expect(wrapper.find("[data-test=loading]").exists()).toBe(true);
  });
});

describe("Alertes, adresse par compte (docs/65 §3)", () => {
  it("un site demande de confirmer : la famille « À confirmer », le panneau ouvre le lien ; la note du filtre Gmail", async () => {
    const pending = {
      search_id: 1,
      site: "jobup",
      subject: "Confirmez votre alerte",
      received_at: "2026-10-16T08:00:00Z",
      url: "https://jobs.example/confirm?t=1",
    };
    const base = page([search(1, [cell("jobup", { status: "created", created_at: new Date().toISOString() })])]);
    const data = { ...base, personal_address: true, to_confirm: [pending] };
    POST.mockResolvedValue({ data: { ...data, to_confirm: [] } });
    const wrapper = await mountView(data);
    expect(wrapper.find("[data-test=alerts-family-confirm] .alerts-family-title").text()).toBe("À confirmer · 1");
    expect(wrapper.find("[data-test=alerts-family-confirm] .alerts-family-help").text()).toContain("jobup attend ta confirmation");
    expect(wrapper.find("[data-test=alert-card-1-jobup] .block-row-aside").text().replace(/^, /, "")).toBe("Confirmation demandée");
    expect(wrapper.find("[data-test=alerts-note]").text()).toContain("transférés par ton filtre Gmail");
    await wrapper.find("[data-test=alert-card-1-jobup]").trigger("click");
    const link = wrapper.find("[data-test=alert-confirm]");
    expect(link.attributes("href")).toBe("https://jobs.example/confirm?t=1");
    link.element.addEventListener("click", (e) => e.preventDefault());
    await link.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/confirmations/{search_id}", {
      params: { path: { search_id: 1 } },
    });
    expect(wrapper.find("[data-test=alerts-family-confirm]").exists()).toBe(false);
  });
});

describe("Alertes, où vont les e-mails des sites (docs/113)", () => {
  it("dit à l'invité que les codes passent par la boîte de jobA1 ; rien pour l'exploitant", async () => {
    const received = [search(1, [cell("jobup", { status: "received", received_at: new Date().toISOString() })])];
    const guest = await mountView({ ...page(received), personal_address: true, guest_mailbox: true });
    expect(guest.find("[data-test=site-code-row]").text()).toContain("la boîte de jobA1");
    const owner = await mountView({ ...page(received), personal_address: false, guest_mailbox: false });
    expect(owner.find("[data-test=site-code-row]").text()).not.toContain("jobA1");
  });
});

describe("Alertes, une colonne (planche « 6. Alertes »)", () => {
  it("les recherches, puis les messages des sites, puis les alertes reçues", async () => {
    const received = [search(1, [cell("jobup", { status: "received", received_at: new Date().toISOString() })])];
    const wrapper = await mountView(page(received));
    const order = wrapper.findAll("[data-test=alert-searches], .alerts-section").map((s) => s.attributes("data-test"));
    expect(order).toEqual(["alert-searches", "site-mail", "received-alerts"]);
    expect(wrapper.findAll(".alerts-section h2").map((h) => h.text())).toEqual(["Messages des sites", "Alertes reçues"]);
  });
});

describe("Alertes, un site en un geste (docs/121 §B.2)", () => {
  it("ouvrir le site copie l'adresse d'avance", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const todo = { ...page([search(1, [cell("jobup"), cell("linkedin")])]), mailbox: "alertes+lea-abc12345@joba1.ch", personal_address: true };
    PUT.mockResolvedValue({ data: todo });
    const wrapper = await mountView(todo);
    await wrapper.find("[data-test=wizard-next]").trigger("click");
    await flushPromises();
    await wrapper.find("[data-test=wizard-open]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("alertes+lea-abc12345@joba1.ch");
    expect(wrapper.find("[data-test=alerts-wizard]").text()).toContain("Adresse copiée");
  });
});

describe("Alertes, depuis la recherche globale (série du 27.10, point 2)", () => {
  it("?recherche= met en avant la carte de la recherche ; ?gerer=1 ouvre le tableau", async () => {
    const { createMemoryHistory, createRouter } = await import("vue-router");
    const data = page([search(1, [cell("jobup", { status: "received", received_at: new Date().toISOString() })])]);
    GET.mockResolvedValue({ data });
    for (const [query, check] of [
      ["?recherche=devops", (w: ReturnType<typeof mount>) => expect(w.find("[data-test=alert-card-1-jobup]").classes()).toContain("highlighted")],
      ["?gerer=1", (w: ReturnType<typeof mount>) => expect(w.find("[data-test=close-manage]").exists()).toBe(true)],
    ] as const) {
      const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
      await router.push(`/candidatures/alertes${query}`);
      const wrapper = mount(AlertsView, { global: { plugins: [router], stubs: { teleport: true, AlertsPanel: true } } });
      await flushPromises();
      check(wrapper);
      wrapper.unmount();
    }
  });
});
