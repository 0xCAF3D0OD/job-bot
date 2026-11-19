// « Faire le point » en page entière (planche FairePoint, accord de Kevin du 18.11.2026).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import FairePointView from "./FairePointView.vue";

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
  feeling: null,
  next_step: null,
  notes: null,
  follow_up_on: "2026-11-19",
};

async function mountView(data: object | null = debrief) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/entretien/:id/faire-le-point", component: FairePointView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/candidatures/suivi");
  await router.push("/entretien/7/faire-le-point");
  GET.mockResolvedValue({ data: data ?? undefined });
  const wrapper = mount(FairePointView, { global: { plugins: [router] }, attachTo: document.body });
  await flushPromises();
  return { wrapper, router };
}

describe("FairePointView", () => {
  it("l'entretien en haut, puis le ressenti, la suite et les notes ; la relance seulement en attente d'une réponse", async () => {
    const { wrapper } = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/applications/{application_id}/debrief", { params: { path: { application_id: 7 } } });
    expect(wrapper.find("h1").text()).toBe("Faire le point");
    const meeting = wrapper.find("[data-test=faire-point-meeting]").text();
    expect(meeting).toContain("NOV");
    expect(meeting).toContain("Entretien · DevOps Engineer");
    expect(meeting).toContain("Alpstack · jeudi 12 nov., 14 h");
    expect(wrapper.findAll("[role=radio]").map((b) => b.text())).toEqual([
      "Bien",
      "Moyen",
      "Pas bien",
      "J’attends une réponse",
      "Un 2e entretien est prévu",
      "On m’a dit non",
    ]);
    expect(wrapper.find("[data-test=faire-point-follow-up]").exists()).toBe(false);
    await wrapper.find("[data-test=next-reponse]").trigger("click");
    expect(wrapper.find("[data-test=faire-point-follow-up]").text()).toBe("Relance conseillée le 19 nov. si rien d’ici là");
    await wrapper.find("[data-test=next-refus]").trigger("click");
    expect(wrapper.find("[data-test=faire-point-follow-up]").exists()).toBe(false);
    expect(wrapper.find("[data-test=next-refus]").attributes("aria-checked")).toBe("true");
    wrapper.unmount();
  });

  it("enregistre les trois réponses puis revient d'où l'on vient ; le ressenti est demandé", async () => {
    const { wrapper, router } = await mountView();
    await wrapper.find("[data-test=faire-point-save]").trigger("click");
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=faire-point-error]").text()).toContain("bien, moyen ou pas bien");
    expect(document.activeElement?.getAttribute("data-test")).toBe("feeling-bien");
    await wrapper.find("[data-test=feeling-moyen]").trigger("click");
    await wrapper.find("[data-test=next-reponse]").trigger("click");
    await wrapper.find("[data-test=faire-point-notes]").setValue("Équipe de 6");
    PUT.mockResolvedValue({ data: { ...debrief, feeling: "moyen" } });
    await wrapper.find("[data-test=faire-point-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}/debrief", {
      params: { path: { application_id: 7 } },
      body: { feeling: "moyen", next_step: "reponse", notes: "Équipe de 6" },
    });
    expect(router.currentRoute.value.path).toBe("/candidatures/suivi");
    wrapper.unmount();
  });

  it("reprend un point déjà fait", async () => {
    const { wrapper } = await mountView({ ...debrief, feeling: "bien", next_step: "entretien", notes: "Déjà noté" });
    expect(wrapper.find("[data-test=feeling-bien]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=next-entretien]").attributes("aria-checked")).toBe("true");
    expect((wrapper.find("[data-test=faire-point-notes]").element as HTMLTextAreaElement).value).toBe("Déjà noté");
    wrapper.unmount();
  });

  it("candidature supprimée ou sans entretien : Envoyées, sans erreur", async () => {
    const { router, wrapper } = await mountView(null);
    expect(router.currentRoute.value.path).toBe("/candidatures/suivi");
    wrapper.unmount();
  });
});
