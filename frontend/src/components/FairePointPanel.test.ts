// « Faire le point » dans le panneau de droite de Rendez-vous (planche FairePointOrdinateur, accord de Kevin du 19.11.2026).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FairePointPanel from "./FairePointPanel.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) } }));
afterEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

const debrief = {
  application_id: 7,
  company: "Alpstack",
  job_title: "DevOps Engineer",
  interview_at: "2026-11-12T13:00:00Z",
  feeling: "moyen",
  next_step: "reponse",
  notes: "Équipe de 6",
  follow_up_on: "2026-11-19",
};

async function mountPanel(source: { kind: "application" | "interview"; id: number }, withTime = true) {
  GET.mockResolvedValue({ data: debrief });
  const wrapper = mount(FairePointPanel, { props: { source, withTime, done: source.kind === "interview" }, attachTo: document.body });
  await flushPromises();
  return wrapper;
}

describe("FairePointPanel", () => {
  it("le point du jour prévu : la ligne de l'entretien, prérempli, la relance en attente d'une réponse", async () => {
    const wrapper = await mountPanel({ kind: "application", id: 7 });
    expect(GET).toHaveBeenCalledWith("/api/applications/{application_id}/debrief", { params: { path: { application_id: 7 } } });
    expect(wrapper.find("h2").text()).toBe("Faire le point");
    expect(wrapper.find("[data-test=fpo-line]").text()).toBe("Entretien · DevOps Engineer · Alpstack, jeudi 12 nov., 14 h");
    expect(wrapper.find("[data-test=fpo-feeling-moyen]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=fpo-next-reponse]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=fpo-follow-up]").text()).toBe("Relance conseillée le 19 nov. si rien d’ici là");
    expect((wrapper.find("[data-test=fpo-notes]").element as HTMLTextAreaElement).value).toBe("Équipe de 6");
    wrapper.unmount();
  });

  it("un retour fait se met à jour par son propre point, puis annonce l'enregistrement", async () => {
    const wrapper = await mountPanel({ kind: "interview", id: 9 }, false);
    expect(GET).toHaveBeenCalledWith("/api/interviews/{interview_id}/debrief", { params: { path: { interview_id: 9 } } });
    expect(wrapper.find("[data-test=fpo-line]").text()).toBe("Entretien · DevOps Engineer · Alpstack, jeudi 12 nov.");
    PUT.mockResolvedValue({ data: debrief });
    await wrapper.find("[data-test=fpo-feeling-bien]").trigger("click");
    await wrapper.find("[data-test=fpo-next-refus]").trigger("click");
    await wrapper.find("[data-test=fpo-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/interviews/{interview_id}/debrief", {
      params: { path: { interview_id: 9 } },
      body: { feeling: "bien", next_step: "refus", notes: "Équipe de 6" },
    });
    expect(wrapper.emitted("saved")).toHaveLength(1);
    expect(wrapper.find("[data-test=fpo-follow-up]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("sans ressenti : un message, rien n'est envoyé", async () => {
    GET.mockResolvedValue({ data: { ...debrief, feeling: null } });
    const wrapper = mount(FairePointPanel, { props: { source: { kind: "application", id: 7 }, withTime: true, done: false }, attachTo: document.body });
    await flushPromises();
    await wrapper.find("[data-test=fpo-save]").trigger("click");
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=fpo-error]").text()).toContain("bien, moyen ou pas bien");
    wrapper.unmount();
  });
});
