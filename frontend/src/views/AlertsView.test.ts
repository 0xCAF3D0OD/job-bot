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

describe("Alertes, la page (planche « 6. Alertes », 1.6.70)", () => {
  it("la conclusion, la bande de l'alerte muette, une carte par recherche, une ligne par site", async () => {
    const wrapper = await mountView(
      page([
        search(1, [cell("jobup", { status: "received", received_at: new Date(Date.now() - 2 * DAY).toISOString() }), cell("linkedin")]),
        search(2, [cell("jobup"), cell("linkedin", { status: "created", created_at: new Date(Date.now() - 4 * DAY).toISOString() })]),
      ]),
    );
    expect(wrapper.find("[data-test=alerts-wizard]").exists()).toBe(false);
    // La conclusion en haut (1.6.22) : le nombre en accent, la dernière alerte reçue.
    const sentence = wrapper.find("[data-test=alerts-sentence]");
    expect(sentence.find("strong").text()).toBe("2 recherches");
    expect(sentence.text()).toMatch(/^2 recherches suivies, la dernière alerte reçue le /);
    // La bande (§3) : LinkedIn n'a rien reçu 4 jours après sa création.
    const band = wrapper.find("[data-test=action-band]");
    expect(band.text()).toContain("LinkedIn n'a encore rien reçu.");
    expect(band.text()).toContain("Ta recherche « Kubernetes » y existe depuis 4 jours");
    expect(wrapper.find("[data-test=action-band-action]").text()).toBe("Vérifier l'alerte");
    // Une carte par recherche, ses lieux, l'état ; une ligne par site.
    const devops = wrapper.find("[data-test=alert-search-1]");
    expect(devops.find(".setting-row-title").text()).toBe("DevOps");
    expect(devops.find(".setting-row-description").text()).toBe("Lausanne");
    expect(devops.find("[data-test=search-state]").text()).toBe("Reçue · jobup");
    expect(devops.find("[data-test=site-jobup]").text()).toContain("Reçue le");
    expect(devops.find("[data-test=create-linkedin]").text()).toBe("Créer");
    const kube = wrapper.find("[data-test=alert-search-2]");
    expect(kube.find("[data-test=site-linkedin]").text()).toContain("Rien reçu depuis la création");
    expect(kube.find("[data-test=site-linkedin] .alert-state").classes()).toContain("silent");
    // « Créer » ouvre le pas à pas sur ce site, pour cette recherche.
    await devops.find("[data-test=create-linkedin]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Crée l'alerte sur LinkedIn");
    expect(wrapper.findAll("[data-test=wizard-open]").map((a) => a.text())).toEqual([expect.stringContaining("DevOps")]);
    await wrapper.find("[data-test=close-wizard]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alert-search-1]").exists()).toBe(true);
  });

  it("tout va bien : pas de bande ; « + Ajouter » ajoute une recherche", async () => {
    const one = page([search(1, [cell("jobup", { status: "received", received_at: new Date(Date.now() - DAY).toISOString() })])]);
    POST.mockResolvedValue({ data: page([...one.searches, search(2, [cell("jobup")])]) });
    const wrapper = await mountView(one);
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=alert-searches] h2").text()).toBe("Recherches suivies");
    await wrapper.find("[data-test=add-search]").trigger("click");
    await wrapper.find("[data-test=add-search-terms]").setValue("Kubernetes");
    await wrapper.find("[data-test=add-search-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "Kubernetes", location: null } });
    expect(wrapper.find("[data-test=alert-search-2]").exists()).toBe(true);
  });

  it("sans alerte reçue : la phrase le dit", async () => {
    const day = new Date(Date.now() - DAY).toISOString();
    const wrapper = await mountView(page([search(1, [cell("jobup", { status: "created", created_at: day })])]));
    expect(wrapper.find("[data-test=alerts-sentence]").text()).toBe("1 recherche suivie, aucune alerte reçue pour l'instant.");
    expect(wrapper.find("[data-test=site-jobup]").text()).toContain("En attente du premier envoi");
  });

  it("des blocs de chargement tant que la page charge (règles §6)", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    const wrapper = mount(AlertsView);
    await flushPromises();
    expect(wrapper.find("[data-test=loading]").exists()).toBe(true);
  });
});

describe("Alertes, adresse par compte (docs/65 §3)", () => {
  it("un site demande de confirmer : la bande ouvre le lien, puis s'en va", async () => {
    const pending = {
      search_id: 9,
      site: "jobsch",
      subject: "Confirmez votre alerte",
      received_at: "2026-10-16T08:00:00Z",
      url: "https://jobs.example/confirm?t=1",
    };
    const data = { ...page([search(1, [cell("jobup", { status: "received", received_at: new Date().toISOString() })])]), to_confirm: [pending] };
    POST.mockResolvedValue({ data: { ...data, to_confirm: [] } });
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    const wrapper = await mountView(data);
    expect(wrapper.find("[data-test=action-band]").text()).toContain("attend ta confirmation");
    await wrapper.find("[data-test=action-band-action]").trigger("click");
    await flushPromises();
    expect(open).toHaveBeenCalledWith("https://jobs.example/confirm?t=1", "_blank", "noopener,noreferrer");
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/confirmations/{search_id}", {
      params: { path: { search_id: 9 } },
    });
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    open.mockRestore();
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
    const order = wrapper.findAll(".alerts-section").map((s) => s.attributes("data-test"));
    expect(order).toEqual(["alert-searches", "site-mail", "received-alerts"]);
    expect(wrapper.findAll(".alerts-section h2").map((h) => h.text())).toEqual(["Recherches suivies", "Messages des sites", "Alertes reçues"]);
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
