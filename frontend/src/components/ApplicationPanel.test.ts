// La ligne de relance de la fiche candidature (revue de l'étape 7c) : reprise de l'ancienne étape « Suivre ».
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ApplicationPanel from "./ApplicationPanel.vue";

const PATCH = vi.fn();
vi.mock("../api/client", () => ({ api: { PATCH: (...a: unknown[]) => PATCH(...a), GET: vi.fn().mockResolvedValue({ data: [] }) } }));
afterEach(() => vi.resetAllMocks());

const application = {
  id: 3,
  offer_id: 7,
  sent_at: "2026-10-02",
  method: "electronique",
  assigned_by_orp: false,
  company: "Exemple SA",
  job_title: "Ingénieur DevOps",
  status: "en_attente",
  follow_up_on: null,
  interviews: [],
  contacts: [],
  orp_month: "2026-10",
  reminded_at: null,
  created_at: "2026-10-02T10:00:00Z",
  letter_draft_id: null,
  cv_draft_id: null,
};

function mountPanel(overrides: Record<string, unknown> = {}) {
  return mount(ApplicationPanel, {
    props: { application: { ...application, ...overrides } as never },
    global: { stubs: { teleport: true, ContactsPanel: true, JobRoomDeclared: true } },
  });
}

describe("La relance dans la fiche candidature", () => {
  it("par défaut 10 jours après l'envoi ; « Changer » enregistre un jour entre 5 et 30 jours", async () => {
    const wrapper = mountPanel();
    const line = () => wrapper.find("[data-test=panel-remind]");
    expect(line().text()).toMatch(/^Relance : le 12 octobre( 2026)? ·\s+Changer le jour de la relance$/);
    await wrapper.find("[data-test=remind-change]").trigger("click");
    const input = wrapper.find<HTMLInputElement>("[data-test=remind-date]");
    expect(input.element.value).toBe("2026-10-12");
    expect(input.attributes("min")).toBe("2026-10-07");
    expect(input.attributes("max")).toBe("2026-11-01");

    // Hors limites : le serveur refuse, le message le dit.
    PATCH.mockResolvedValueOnce({ data: undefined, error: { detail: "entre 5 et 30 jours après l'envoi" } });
    await input.setValue("2026-12-01");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Choisis un jour entre 5 et 30 jours après l'envoi.");
    expect(input.attributes("aria-invalid")).toBe("true");

    PATCH.mockResolvedValueOnce({ data: { ...application, follow_up_on: "2026-10-20" } });
    await input.setValue("2026-10-20");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(PATCH).toHaveBeenLastCalledWith("/api/applications/{application_id}/follow-up-date", {
      params: { path: { application_id: 3 } },
      body: { follow_up_on: "2026-10-20" },
    });
    expect(line().text()).toMatch(/^Relance : le 20 octobre/);
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("le jour choisi est repris ; une fois répondue, « Plus de relance prévue » sans bouton", () => {
    expect(mountPanel({ follow_up_on: "2026-10-15" }).find("[data-test=panel-remind]").text()).toMatch(/^Relance : le 15 octobre/);
    const answered = mountPanel({ status: "entretien" });
    expect(answered.find("[data-test=panel-remind]").text()).toBe("Plus de relance prévue");
    expect(answered.find("[data-test=remind-change]").exists()).toBe(false);
  });
});
