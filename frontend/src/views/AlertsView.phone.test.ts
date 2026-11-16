import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

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
  it("l’étape 2 reste dans la carte de l’assistant, pas de panneau", async () => {
    const todo = page([search(1, [cell("jobup"), cell("linkedin")])]);
    PUT.mockResolvedValue({ data: todo });
    const wrapper = await mountView(todo);
    await wrapper.find("[data-test=wizard-next]").trigger("click");
    await flushPromises();
    expect(wrapper.find(".alert-site-panel").exists()).toBe(false);
    expect(wrapper.find("[data-test=alerts-wizard]").text()).toContain("Crée l’alerte sur jobup");
    expect(wrapper.find("[data-test=wizard-site-count]").text()).toBe("· site 1 sur 2");
    expect(wrapper.find("[data-test=wizard-skip]").classes()).toContain("secondary");
    await wrapper.find("[data-test=wizard-site-done]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Crée l’alerte sur LinkedIn");
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
