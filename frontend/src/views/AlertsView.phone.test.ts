import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AlertsView from "./AlertsView.vue";

vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", useNarrow: () => ({ phone: ref(true) }), usePhone: () => ({ phone: ref(true) }) }));

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

// Téléphone : le pas à pas reste en pleine page, sans le panneau de l'ordinateur (consigne de Kevin du 13.11 :
// « Rien ne change sur téléphone »).
describe("Alertes sur téléphone : le pas à pas inchangé", () => {
  it("aucune alerte : AlertesVide (§72c), « Créer une alerte » ouvre la création des premiers pas", async () => {
    const todo = page([search(1, [cell("jobup"), cell("linkedin")])]);
    GET.mockResolvedValue({ data: todo });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    const wrapper = mount(AlertsView, { global: { plugins: [router], stubs: { teleport: true } } });
    await flushPromises();
    const empty = wrapper.get("[data-test=alerts-empty]");
    expect(empty.find("h2").text()).toBe("Pas encore d’alerte");
    expect(empty.text()).toContain("Environ 2 minutes");
    expect(empty.get("[data-test=alerts-empty-create]").text()).toBe("Créer une alerte");
    expect(empty.get("[data-test=alerts-empty-create]").attributes("href")).toBe("/bienvenue?etape=alerte&retour=alertes");
    expect(wrapper.find("[data-test=alerts-wizard]").exists()).toBe(false);
  });

  it("la carte « À créer » ouvre la feuille « Alerte », puis le pas à pas en pleine page", async () => {
    const data = page([search(1, [cell("jobup", { status: "received", received_at: new Date().toISOString() }), cell("linkedin")])]);
    const wrapper = await mountView(data);
    await wrapper.find("[data-test=alert-card-1-linkedin]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=alert-sheet]").text()).toContain("À créer sur LinkedIn");
    await wrapper.find("[data-test=alert-create]").trigger("click");
    await flushPromises();
    expect(wrapper.find(".alert-site-panel").exists()).toBe(false);
    expect(wrapper.find("[data-test=alerts-wizard]").text()).toContain("Crée l’alerte sur LinkedIn");
  });
});
