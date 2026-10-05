import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

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

function mockGet(items: unknown[], target: number | null): void {
  GET.mockImplementation((path: string, opts: { params: { query: { month: string } } }) =>
    Promise.resolve({
      data:
        path === "/api/applications/summary"
          ? { month: opts.params.query.month, count: items.length, target }
          : items,
    }),
  );
}

describe("ApplicationsView", () => {
  it("liste les candidatures du mois et le compteur ORP", async () => {
    mockGet([application], 20);
    const wrapper = mount(ApplicationsView);
    await flushPromises();
    expect(wrapper.findAll("[data-test=application]")).toHaveLength(1);
    expect(wrapper.text()).toContain("Acme SA");
    expect(wrapper.find("[data-test=goal]").text()).toContain("1 / 20");
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("5");
  });

  it("sans objectif : invite à le saisir", async () => {
    mockGet([], null);
    const wrapper = mount(ApplicationsView);
    await flushPromises();
    expect(wrapper.find("[data-test=goal]").text()).toContain("Réglages");
    expect(wrapper.text()).toContain("Aucune candidature");
  });

  it("changer de mois recharge la liste", async () => {
    mockGet([], 20);
    const wrapper = mount(ApplicationsView);
    await flushPromises();
    const before = GET.mock.calls.length;
    await wrapper.find("[data-test=prev-month]").trigger("click");
    await flushPromises();
    expect(GET.mock.calls.length).toBe(before + 2);
  });

  it("changer le statut garde la date d'entretien", async () => {
    mockGet([application], 20);
    PUT.mockResolvedValue({ data: { ...application, status: "entretien" } });
    const wrapper = mount(ApplicationsView);
    await flushPromises();
    await wrapper.find("[data-test=status-select]").setValue("entretien");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications/{application_id}");
    expect(opts.body.status).toBe("entretien");
    expect(opts.body.interview_at).toBe(application.interview_at);
  });

  it("ajout manuel : crée une candidature sans offre", async () => {
    mockGet([], 20);
    POST.mockResolvedValue({ data: application });
    const wrapper = mount(ApplicationsView);
    await flushPromises();
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
