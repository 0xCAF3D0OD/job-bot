// ④ Suivre (docs/124 §G).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import FollowStep from "./FollowStep.vue";

const GET = vi.fn();
const PATCH = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PATCH: (...a: unknown[]) => PATCH(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));
afterEach(() => vi.resetAllMocks());

const application = {
  id: 5, offer_id: 9, sent_at: "2026-10-20", method: "electronique", company: "Acme SA", job_title: "DevOps",
  status: "en_attente", orp_month: "2026-10", follow_up_on: null, contact_name: null, contacts: [], company_address: null,
};

function answer(missing: string[], app: Record<string, unknown> = {}) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/applications" ? [{ ...application, ...app }] : { rows: [{ application_id: 5, missing }] } }),
  );
}

async function mountStep() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(FollowStep, { props: { offerId: 9 }, global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("FollowStep", () => {
  it("la relance à 10 jours, la preuve ORP à compléter, le contact à ajouter", async () => {
    answer(["adresse de l'entreprise"]);
    const wrapper = await mountStep();
    expect(GET).toHaveBeenCalledWith("/api/applications", { params: { query: { offer: 9 } } });
    expect(wrapper.find("[data-test=follow-remind]").text()).toContain("Le 30 octobre, si l'employeur n'a pas répondu.");
    expect(wrapper.find("[data-test=follow-orp]").text()).toContain("Il manque adresse de l'entreprise.");
    await wrapper.find("[data-test=follow-add-contact]").trigger("click");
    expect(wrapper.emitted("addContact")).toBeTruthy();
  });

  it("changer la date de relance, compléter l'adresse sur place", async () => {
    answer(["adresse de l'entreprise"]);
    PATCH.mockResolvedValue({ data: { ...application, follow_up_on: "2026-11-05" } });
    PUT.mockResolvedValue({ data: application });
    const wrapper = await mountStep();
    await wrapper.find("[data-test=follow-change-date]").trigger("click");
    const date = wrapper.find("[data-test=follow-date]");
    expect(date.attributes("min")).toBe("2026-10-25");
    expect(date.attributes("max")).toBe("2026-11-19");
    await date.setValue("2026-11-05");
    await wrapper.find("[data-test=follow-save]").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/applications/{application_id}/follow-up-date", { params: { path: { application_id: 5 } }, body: { follow_up_on: "2026-11-05" } });
    expect(wrapper.find("[data-test=follow-remind]").text()).toContain("Le 5 novembre");
    await wrapper.find("[data-test=follow-complete]").trigger("click");
    await wrapper.find("[data-test=follow-address]").setValue("Rue du Lac 1, 1000 Lausanne");
    answer([]);
    await wrapper.find("[data-test=follow-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}", expect.objectContaining({ body: expect.objectContaining({ company_address: "Rue du Lac 1, 1000 Lausanne", status: "en_attente" }) }));
    expect(wrapper.find("[data-test=follow-orp]").text()).toContain("Complète");
  });

  it("le contact connu, et plus de relance une fois relancée", async () => {
    answer([], { contact_name: "Sam Exemple", status: "relancee" });
    const wrapper = await mountStep();
    expect(wrapper.find("[data-test=follow-contact]").text()).toContain("Sam Exemple");
    expect(wrapper.find("[data-test=follow-remind]").text()).toContain("Plus de relance prévue.");
    expect(wrapper.find("[data-test=follow-change-date]").exists()).toBe(false);
  });
});
