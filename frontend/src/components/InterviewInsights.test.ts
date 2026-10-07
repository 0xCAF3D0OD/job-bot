import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import InterviewInsights from "./InterviewInsights.vue";
import InterviewPreparation from "./InterviewPreparation.vue";

const GET = vi.fn();
const PUT = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

function insights(extra: Record<string, unknown> = {}) {
  return {
    count: 2,
    average_rating: 3,
    questions: [
      { text: "Vos points faibles ?", count: 1, difficult: 1 },
      { text: "Présentez-vous", count: 2, difficult: 0 },
    ],
    went_well: [{ company: "Autre SA", held_at: "2026-10-06", text: "Bonne démo" }],
    went_badly: [{ company: "Exemple SA", held_at: null, text: "Réponse floue" }],
    to_prepare: [{ text: "Exemple chiffré", done: false }],
    missed_questions: [{ company: "Exemple SA", held_at: null, text: "Taille de l'équipe ?" }],
    employer_feedback: [],
    coaching: null,
    can_coach: true,
    ...extra,
  };
}
const coaching = {
  created_at: "2026-10-07T10:00:00Z",
  application_id: 3,
  pistes: ["Prépare un exemple chiffré"],
  answers: [{ question: "Vos points faibles ?", answer: "Je…" }],
  questions_to_ask: ["Quelle équipe ?"],
};

describe("Mes enseignements (docs/23 §3)", () => {
  it("questions qui reviennent, à préparer coché, pistes de l'IA à la demande", async () => {
    GET.mockResolvedValue({ data: insights() });
    PUT.mockResolvedValue({ data: insights({ to_prepare: [{ text: "Exemple chiffré", done: true }] }) });
    POST.mockResolvedValue({ data: insights({ coaching }) });
    const wrapper = mount(InterviewInsights);
    await flushPromises();
    expect(wrapper.find("summary").text()).toContain("2 entretien(s), ressenti moyen 3/5");
    expect(wrapper.find("[data-test=insight-questions]").text()).toContain("difficile 1×");
    await wrapper.find("[data-test=prepare-item]").setValue(true);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/interviews/insights/prepared", { body: { text: "Exemple chiffré", done: true } });
    await wrapper.find("[data-test=coach]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interviews/coach", { body: {} });
    expect(wrapper.find("[data-test=coaching]").text()).toContain("Prépare un exemple chiffré");
  });

  it("aucun entretien : la section reste visible et explique comment la remplir", async () => {
    GET.mockResolvedValue({ data: insights({ count: 0 }) });
    const wrapper = mount(InterviewInsights);
    await flushPromises();
    expect(wrapper.find("summary").text()).toBe("Mes enseignements");
    expect(wrapper.find("[data-test=insights-empty]").text()).toContain("Faire le point sur l'entretien");
    expect(wrapper.find("[data-test=coach]").exists()).toBe(false);
  });
});

describe("Préparer l'entretien (docs/23 §3)", () => {
  it("poste, questions difficiles, à préparer, pistes pour cet entretien", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data: path === "/api/interviews/insights" ? insights() : { summary_role: "Plateformes Kubernetes", summary_asks: "3 ans DevOps" },
      }),
    );
    POST.mockResolvedValue({ data: insights({ coaching }) });
    const application = {
      id: 3,
      offer_id: 7,
      company: "Exemple SA",
      job_title: "Ingénieur DevOps",
      interview_at: "2026-10-20T09:00:00Z",
      interviews: [],
    };
    const wrapper = mount(InterviewPreparation, { props: { application: application as never } });
    await flushPromises();
    expect(wrapper.text()).toContain("Plateformes Kubernetes");
    expect(wrapper.find("[data-test=prep-difficult]").text()).toContain("Vos points faibles ?");
    expect(wrapper.find("[data-test=prep-todo]").text()).toContain("Exemple chiffré");
    await wrapper.find("[data-test=prep-coach]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interviews/coach", { body: { application_id: 3 } });
    expect(wrapper.find("[data-test=coaching]").text()).toContain("Quelle équipe ?");
  });
});
