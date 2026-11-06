import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: () => ({ phone: ref(true) }),
  useNarrow: () => ({ phone: ref(true) }),
}));
const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn(), DELETE: vi.fn() },
}));

import OrpMeetingView from "./OrpMeetingView.vue";

// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6.11.2026).
const EMPTY = { outcome_at: null, agreed_target: null, measures: [], assignments: null, note: null, asked: [], next_starts_at: null, sheet_text: null };
const PREP = {
  summaries: [],
  works: null,
  blockers: ["Formulaires en ligne : 0 réponse sur 9."],
  missing: [{ skill: "Terraform", count: 14, training_id: null, training_title: null }],
  offers: 22,
  questions: [
    { key: "funding:3", text: "Financer la formation Terraform", checked: true },
    { key: "intermediate", text: "Déclarer mon gain intermédiaire", checked: false },
  ],
  obligations: [],
  months: [{ month: "2099-11", count: 6, target: 10, answered: 0, interviews: 0 }],
  has_applications: true,
};
const MEETING = { id: 1, starts_at: "2099-11-10T08:30:00Z", place: "ORP Renens", advisor: null, ...EMPTY };
const PAST = {
  ...MEETING,
  id: 2,
  starts_at: "2026-10-13T08:00:00Z",
  outcome_at: "2026-10-13T10:00:00Z",
  agreed_target: 10,
  measures: [{ text: "Cours Terraform", training_id: null }],
  next_starts_at: "2099-11-10T08:30:00Z",
};
const interview = (id: number, at: string) => ({
  id,
  company: `Entreprise ${id}`,
  job_title: `Poste ${id}`,
  status: "entretien",
  interview_at: at,
  company_address: id === 7 ? "Avenue de la Gare 12, Lausanne" : null,
  interviews: [],
});

function serve(page: object, applications: object[] = []): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/applications" ? { data: applications } : path === "/api/orp-meeting" ? { data: page } : { data: null }),
  );
}

async function open(query = "") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/candidatures/rendez-vous-orp", component: OrpMeetingView }],
  });
  await router.push(`/candidatures/rendez-vous-orp${query}`);
  const wrapper = mount(OrpMeetingView, { global: { plugins: [router], stubs: { InterviewPreparation: true, OrpOutcomeForm: true } } });
  await flushPromises();
  return { wrapper, router };
}

afterEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

describe("Rendez-vous sur téléphone", () => {
  it("« À venir » : l'ORP et les entretiens mêlés, par date ; puis « Derniers rendez-vous ORP »", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [PAST], target: 10, trainings: [] }, [
      interview(7, "2099-11-16T09:00:00Z"),
      interview(8, "2099-11-08T13:00:00Z"),
    ]);
    const { wrapper } = await open();
    const upcoming = wrapper.get("[data-test=rdv-upcoming]");
    expect(upcoming.get("h2").text()).toBe("À venir3 rendez-vous");
    const order = upcoming.findAll("article").map((a) => a.attributes("data-test"));
    expect(order).toEqual(["rdv-interview-8", "rdv-orp", "rdv-interview-7"]);
    // Le bloc date est décoratif ; la date est aussi dite en texte.
    const orp = wrapper.get("[data-test=rdv-orp]");
    expect(orp.get(".rdv-date").attributes("aria-hidden")).toBe("true");
    expect(orp.text()).toContain("Mardi 10 novembre, 9 h 30 · ORP Renens");
    expect(orp.text()).toContain("Ta feuille est prête");
    expect(orp.findAll("[data-test=rdv-lines] li").map((li) => li.text())).toEqual([
      "Ton mois6 recherches sur 10",
      "Ce qui bloqueFormulaires en ligne : 0 réponse sur 9",
      "Ce qui te manqueTerraform, demandé dans 14 offres sur 22",
    ]);
    expect(wrapper.get("[data-test=rdv-interview-7]").text()).toContain("Avenue de la Gare 12, Lausanne");
    // La page de l'ordinateur ne s'affiche pas.
    expect(wrapper.find("[data-test=meeting-when]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-questions]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-facts]").exists()).toBe(false);
    const past = wrapper.get("[data-test=rdv-past]");
    expect(past.text()).toContain("Rendez-vous ORP du 13 octobre");
    expect(past.get("[data-test=rdv-agreed]").text()).toContain("Objectif10 recherches par mois");
    expect(past.get("[data-test=rdv-log]").text()).toContain("Carnet ORP1 rendez-vous");
  });

  it("les questions au conseiller, repliées, avec les cases existantes", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] });
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] } });
    const { wrapper } = await open();
    const toggle = wrapper.get("[data-test=rdv-questions]");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    expect(toggle.text()).toContain("1 cochée");
    await toggle.trigger("click");
    expect(toggle.attributes("aria-expanded")).toBe("true");
    await wrapper.get("[data-test=rdv-question-intermediate]").setValue(true);
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/questions", {
      body: { questions: [PREP.questions[0], { ...PREP.questions[1], checked: true }] },
    });
  });

  it("« Voir ma feuille » ouvre la feuille actuelle ; « Imprimer » télécharge le PDF", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [PAST], target: 10, trainings: [] });
    const { wrapper, router } = await open();
    expect(wrapper.get("[data-test=rdv-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf");
    await wrapper.get("[data-test=rdv-sheet]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.feuille).toBe("1");
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-questions]").exists()).toBe(true);
  });

  it("aucun rendez-vous : l'illustration et le formulaire d'avant", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-past]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(wrapper.text()).toContain("Aucun rendez-vous ORP prévu");
  });

  it("un entretien sans rendez-vous ORP : l'entretien à venir, puis le formulaire du rendez-vous", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] }, [interview(8, "2099-11-08T13:00:00Z")]);
    const { wrapper } = await open();
    expect(wrapper.get("[data-test=rdv-upcoming] h2").text()).toBe("À venir1 rendez-vous");
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
  });

  it("le rendez-vous passé : noter ce qui a été convenu, avec le formulaire existant", async () => {
    const started = { ...MEETING, starts_at: "2026-10-13T08:00:00Z" };
    serve({ meeting: started, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    await wrapper.get("[data-test=rdv-note]").trigger("click");
    expect(wrapper.findComponent({ name: "OrpOutcomeForm" }).exists()).toBe(true);
  });

  it("pas encore de candidature : l'écran d'avant", async () => {
    serve({ meeting: null, preparation: { ...PREP, has_applications: false }, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-none-yet]").exists()).toBe(true);
  });
});
