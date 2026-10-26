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
  const wrapper = mount(AlertsView);
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
    expect(wrapper.find("[data-test=journal-toggle]").attributes("open")).toBeUndefined();

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

describe("Alertes, résumé (docs/21 §4)", () => {
  it("un point par recherche, aide seulement pour ce qui n'arrive pas", async () => {
    const wrapper = await mountView(
      page([
        search(1, [cell("jobup", { status: "received", received_at: "2026-10-06T08:00:00Z" }), cell("linkedin")]),
        search(2, [cell("jobup"), cell("linkedin", { status: "created", created_at: new Date(Date.now() - 4 * DAY).toISOString() })]),
      ]),
    );
    expect(wrapper.find("[data-test=alerts-wizard]").exists()).toBe(false);
    // La conclusion en haut (1.6.22) : le nombre en accent, la dernière alerte reçue.
    const sentence = wrapper.find("[data-test=alerts-sentence]");
    expect(sentence.text()).toBe("2 recherches suivies, la dernière alerte reçue le 6 octobre.");
    expect(sentence.find("strong").text()).toBe("2 recherches suivies");
    expect(wrapper.find("[data-test=alerts-summary] h2").text()).toBe("Les alertes");
    const rows = wrapper.findAll("[data-test=summary-row]");
    expect(rows[0]!.classes()).toContain("ok");
    expect(rows[1]!.classes()).toContain("late");
    expect(wrapper.find("[data-test=late-help]").text()).toContain("Rien reçu de LinkedIn");
    expect(wrapper.find("[data-test=late-help] [data-test=hover-note]").attributes("aria-description")).toContain("jobs-noreply@linkedin.com");

    await wrapper.find("[data-test=manage-alerts]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alerts-panel]").exists()).toBe(true);
    await wrapper.find("[data-test=close-manage]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alerts-summary]").exists()).toBe(true);
  });

  it("tout va bien : pas d'aide au transfert", async () => {
    const wrapper = await mountView(page([search(1, [cell("jobup", { status: "received", received_at: "2026-10-06T08:00:00Z" })])]));
    expect(wrapper.find("[data-test=late-help]").exists()).toBe(false);
  });

  it("sans alerte reçue : la phrase le dit", async () => {
    const day = new Date(Date.now() - 4 * DAY).toISOString();
    const wrapper = await mountView(page([search(1, [cell("jobup", { status: "created", created_at: day })])]));
    expect(wrapper.find("[data-test=alerts-sentence]").text()).toBe("1 recherche suivie, aucune alerte reçue pour l'instant.");
  });

  it("des blocs de chargement tant que la page charge (règles §6)", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    const wrapper = mount(AlertsView);
    await flushPromises();
    expect(wrapper.find("[data-test=loading]").exists()).toBe(true);
  });
});

describe("Alertes, adresse par compte (docs/65 §3)", () => {
  it("un site demande de confirmer : le lien, puis la ligne s'en va", async () => {
    const pending = {
      search_id: 9,
      site: "jobsch",
      subject: "Confirmez votre alerte",
      received_at: "2026-10-16T08:00:00Z",
      url: "https://jobs.example/confirm?t=1",
    };
    const data = { ...page([search(1, [cell("jobup", { status: "receiving" })])]), to_confirm: [pending] };
    POST.mockResolvedValue({ data: { ...data, to_confirm: [] } });
    const wrapper = await mountView(data);
    const link = wrapper.find("[data-test=confirm-link]");
    expect(link.attributes("href")).toBe("https://jobs.example/confirm?t=1");
    expect(link.attributes("rel")).toContain("noopener");
    await link.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/confirmations/{search_id}", {
      params: { path: { search_id: 9 } },
    });
    expect(wrapper.find("[data-test=to-confirm]").exists()).toBe(false);
  });
});

describe("Alertes, où vont les e-mails des sites (docs/113)", () => {
  it("dit à l'invité que la boîte de jobA1 range puis efface ; rien pour l'exploitant", async () => {
    const guest = await mountView({ ...page([]), personal_address: true, guest_mailbox: true });
    expect(guest.find("[data-test=guest-mailbox-note]").attributes("aria-description")).toContain("effacés de la boîte une fois rangés");
    const owner = await mountView({ ...page([]), personal_address: false, guest_mailbox: false });
    expect(owner.find("[data-test=guest-mailbox-note]").exists()).toBe(false);
  });
});

describe("Alertes, une colonne (docs/130 §F)", () => {
  it("les alertes, puis les e-mails des sites, puis le journal", async () => {
    const wrapper = await mountView({ ...page([]), personal_address: true, guest_mailbox: true });
    const columns = wrapper.find(".alerts-columns");
    expect(columns.classes()).not.toContain("wide");
    expect(columns.find(".alerts-main h2").text()).toBe("Les alertes");
    expect(columns.find(".alerts-aside [data-test=site-mail]").exists()).toBe(true);
    expect(columns.find(".alerts-aside > h2").text()).toBe("Le détail");
    expect(columns.find(".alerts-journal").exists()).toBe(true);
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
