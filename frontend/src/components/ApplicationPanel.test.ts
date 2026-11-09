// La ligne de relance de la fiche candidature (revue de l'étape 7c) : reprise de l'ancienne étape « Suivre ».
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ApplicationPanel from "./ApplicationPanel.vue";
import { pickDate } from "./DateField.testing";

const PATCH = vi.fn();
vi.mock("../api/client", () => ({ api: { PATCH: (...a: unknown[]) => PATCH(...a), GET: vi.fn().mockResolvedValue({ data: [] }) } }));
// Le jour du test est fixé au lendemain de l'envoi : les dates écrites en dur restent à venir.
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-03T09:00:00"));
});
afterEach(() => {
  vi.useRealTimers();
  vi.resetAllMocks();
});

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
    // La pilule de date (DateField, lot 10) : le jour proposé, et le sélecteur borné entre 5 et 30 jours.
    const pill = () => wrapper.find("[data-test=remind-date] [data-test=dt-date]");
    expect(pill().attributes("aria-label")).toContain("12 octobre");
    await pill().trigger("click");
    const days = wrapper.findAll("[data-test=remind-date] .dt-day");
    const enabled = days.filter((d) => d.attributes("disabled") === undefined).map((d) => d.attributes("data-day"));
    expect(enabled[0]).toBe("2026-10-07");
    await wrapper.find("[data-test=remind-date] [data-test=dt-back]").trigger("click");

    // Le serveur refuse (le jour a changé entre-temps) : le message le dit.
    PATCH.mockResolvedValueOnce({ data: undefined, error: { detail: "entre 5 et 30 jours après l'envoi" } });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Choisis un jour entre 5 et 30 jours après l'envoi.");
    expect(wrapper.find("[data-test=remind-date] .dt-field").attributes("aria-invalid")).toBe("true");

    PATCH.mockResolvedValueOnce({ data: { ...application, follow_up_on: "2026-10-20" } });
    await pickDate(wrapper, "remind-date", "2026-10-20");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(PATCH).toHaveBeenLastCalledWith("/api/applications/{application_id}/follow-up-date", {
      params: { path: { application_id: 3 } },
      body: { follow_up_on: "2026-10-20" },
    });
    expect(line().text()).toMatch(/^Relance : le 20 octobre/);
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("le jour de relance venu, toujours en attente : « Relance à faire », avec « Changer »", () => {
    // Envoyée il y a 12 jours, sans jour choisi : la relance (10 jours après) est passée.
    const day = new Date();
    day.setDate(day.getDate() - 12);
    const sent = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
    const due = mountPanel({ sent_at: sent });
    expect(due.find("[data-test=panel-remind]").text()).toMatch(/^Relance à faire ·\s+Changer le jour de la relance$/);
    expect(due.find("[data-test=remind-change]").exists()).toBe(true);
    // Un jour choisi plus tard : la date revient.
    const later = new Date();
    later.setDate(later.getDate() + 3);
    const laterDay = `${later.getFullYear()}-${String(later.getMonth() + 1).padStart(2, "0")}-${String(later.getDate()).padStart(2, "0")}`;
    expect(mountPanel({ sent_at: sent, follow_up_on: laterDay }).find("[data-test=panel-remind]").text()).toMatch(/^Relance : le /);
  });

  it("le jour choisi est repris ; une fois répondue, « Plus de relance prévue » sans bouton", () => {
    expect(mountPanel({ follow_up_on: "2026-10-15" }).find("[data-test=panel-remind]").text()).toMatch(/^Relance : le 15 octobre/);
    const answered = mountPanel({ status: "entretien" });
    expect(answered.find("[data-test=panel-remind]").text()).toBe("Plus de relance prévue");
    expect(answered.find("[data-test=remind-change]").exists()).toBe(false);
  });
});

describe("Le panneau d'une candidature (téléphone et écrans moyens)", () => {
  it("sans colonnes (téléphone), l'ordre reste : Statut, Documents, Contacts", () => {
    const wrapper = mountPanel({ letter_draft_id: 4 });
    expect(wrapper.find("[data-test=detail-columns]").exists()).toBe(false);
    const order = wrapper.findAll("section").map((s) => s.attributes("data-test"));
    expect(order).toEqual(["section-status", "section-documents", "section-contacts"]);
    expect(wrapper.find("contacts-panel-stub").attributes("part")).toBe("all");
  });
});

describe("« Pour l'ORP » sur ordinateur (lot 18, §10.3)", () => {
  it("le lien ouvre la fiche dans un panneau latéral de 480 px, du mois de la candidature", async () => {
    const wrapper = mount(ApplicationPanel, {
      props: { application: application as never, orpRow: { date: "02.10.2026", declared_at: null, missing: [], job_room: [] } as never },
      global: { stubs: { teleport: true, ContactsPanel: true, JobRoomDeclared: true, OrpFiche: true } },
    });
    expect(wrapper.find("orp-fiche-stub").exists()).toBe(false);
    await wrapper.find("[data-test=orp-fiche-open]").trigger("click");
    const fiche = wrapper.find("orp-fiche-stub");
    expect(fiche.attributes("month")).toBe("2026-10");
    expect(fiche.attributes("applicationid")).toBe("3");
    expect(wrapper.find(".side-panel-480").attributes("aria-label")).toBe("Pour l’ORP");
  });
});
