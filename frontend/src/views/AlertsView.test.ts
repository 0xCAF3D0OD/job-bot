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
    await wrapper.find("[data-test=wizard-next]").trigger("click");

    // Étape 2 : jobup, puis LinkedIn.
    expect(wrapper.text()).toContain("Crée l'alerte sur jobup");
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
    const summary = wrapper.find("[data-test=alerts-summary]");
    expect(summary.text()).toContain("2 recherche(s) suivie(s)");
    expect(summary.text()).toContain("dernière alerte reçue le 6 octobre");
    const rows = wrapper.findAll("[data-test=summary-row]");
    expect(rows[0]!.classes()).toContain("ok");
    expect(rows[1]!.classes()).toContain("late");
    expect(wrapper.find("[data-test=late-help]").text()).toContain("Rien reçu de LinkedIn");
    expect(wrapper.find("[data-test=late-help]").text()).toContain("jobs-noreply@linkedin.com");

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
});
