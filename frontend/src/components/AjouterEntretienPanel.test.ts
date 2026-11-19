// « Ajouter un entretien » dans le panneau de droite de Rendez-vous (planche AjouterEntretienOrdinateur, §72p ; accord de
// Kevin du 19.11.2026).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Application } from "../api/client";
import AjouterEntretienPanel from "./AjouterEntretienPanel.vue";
import DateTimePanel from "./DateTimePanel.vue";

const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));
afterEach(() => POST.mockReset());

const base = {
  id: 7,
  company: "Alpstack",
  job_title: "DevOps Engineer",
  status: "entretien",
  interview_at: null,
  interviews: [],
  planned: [],
} as unknown as Application;

function mountPanel(application: Partial<Application> = {}) {
  return mount(AjouterEntretienPanel, { props: { application: { ...base, ...application } as Application }, attachTo: document.body });
}

describe("AjouterEntretienPanel", () => {
  it("le titre, le poste et l'entreprise ; le tour proposé suit les entretiens déjà connus", () => {
    const first = mountPanel();
    expect(first.find("h2").text()).toBe("Ajouter un entretien");
    expect(first.find("[data-test=aje-line]").text()).toBe("DevOps Engineer · Alpstack");
    expect(first.find("[data-test=aje-round-1]").attributes("aria-checked")).toBe("true");
    first.unmount();
    // Un entretien prévu sans retour : le suivant est le 2e.
    const second = mountPanel({ interview_at: "2026-11-12T13:00:00Z" });
    expect(second.find("[data-test=aje-round-2]").attributes("aria-checked")).toBe("true");
    second.unmount();
    // Le retour du même jour ne compte pas deux fois ; un entretien gardé à côté, si.
    const third = mountPanel({
      interview_at: "2026-11-12T13:00:00Z",
      interviews: [{ id: 3, held_at: "2026-11-12" }] as Application["interviews"],
      planned: [{ id: 4, scheduled_at: "2026-11-05T09:00:00Z", place: null, round: "1" }],
    });
    expect(third.find("[data-test=aje-round-final]").attributes("aria-checked")).toBe("true");
    third.unmount();
  });

  it("sans date ni heure : un message, rien n'est envoyé", async () => {
    const wrapper = mountPanel();
    await wrapper.find("[data-test=aje-add]").trigger("click");
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=aje-when-error]").text()).toBe("Indique la date de l’entretien.");
    wrapper.unmount();
  });

  it("ajoute l'entretien avec le tour, la date et l'heure, le lieu ; puis l'annonce", async () => {
    POST.mockResolvedValue({ response: { ok: true } });
    const wrapper = mountPanel({ interview_at: "2026-11-12T13:00:00Z" });
    await wrapper.find("[data-test=aje-round-final]").trigger("click");
    await wrapper.find("[data-test=dt-date]").trigger("click");
    wrapper.findComponent(DateTimePanel).vm.$emit("confirm", { date: "2026-11-26", time: "14:00" });
    await flushPromises();
    await wrapper.find("[data-test=aje-place]").setValue("Alpstack, Lausanne");
    await wrapper.find("[data-test=aje-add]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/applications/{application_id}/interview-plan", {
      params: { path: { application_id: 7 } },
      body: { round: "final", at: new Date("2026-11-26T14:00").toISOString(), place: "Alpstack, Lausanne" },
    });
    expect(wrapper.emitted("added")).toHaveLength(1);
    wrapper.unmount();
  });

  it("refusé par le serveur : un message, rien d'annoncé", async () => {
    POST.mockResolvedValue({ response: { ok: false } });
    const wrapper = mountPanel();
    await wrapper.find("[data-test=dt-date]").trigger("click");
    wrapper.findComponent(DateTimePanel).vm.$emit("confirm", { date: "2026-11-26", time: "14:00" });
    await flushPromises();
    await wrapper.find("[data-test=aje-add]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=aje-error]").text()).toBe("Entretien non ajouté. Réessaie dans un instant.");
    expect(wrapper.emitted("added")).toBeUndefined();
    wrapper.unmount();
  });
});
