// S'entraîner à l'entretien (docs/75) : choix, échanges, retour.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import InterviewPractice from "./InterviewPractice.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: vi.fn(() => Promise.resolve({})),
  },
}));
afterEach(() => vi.resetAllMocks());

function practice(extra: Record<string, unknown> = {}) {
  return {
    id: 5,
    application_id: 3,
    company: "Exemple SA",
    job_title: "Ingénieur DevOps",
    kind: "technique",
    tone: "bienveillant",
    language: "en",
    status: "en_cours",
    question: 1,
    questions: 5,
    waiting: false,
    turns: [{ role: "recruteur", text: "Tell me about yourself.", question: 1, relance: false, skipped: false }],
    feedback: null,
    cost_chf: 0.01,
    created_at: "2026-10-18T10:00:00Z",
    ...extra,
  };
}

const application = { id: 3, company: "Exemple SA", job_title: "Ingénieur DevOps" } as never;

describe("InterviewPractice", () => {
  it("reprend les choix par défaut, démarre, envoie une réponse avec Entrée", async () => {
    GET.mockResolvedValue({ data: { kind: "technique", language: "en", can_practice: true } });
    POST.mockResolvedValueOnce({ data: practice() });
    const wrapper = mount(InterviewPractice, { props: { application } });
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/interview-practices/defaults", { params: { query: { application_id: 3 } } });
    expect(wrapper.find("[data-test=practice-kind-technique]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=practice-language-en]").attributes("aria-checked")).toBe("true");
    await wrapper.find("[data-test=practice-tone-exigeant]").trigger("click");
    await wrapper.find("[data-test=practice-start]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interview-practices", {
      body: { application_id: 3, kind: "technique", tone: "exigeant", language: "en" },
    });
    expect(wrapper.find("[data-test=practice-progress]").text()).toBe("Question 1 sur 5");

    POST.mockResolvedValueOnce({
      data: practice({
        question: 2,
        turns: [
          ...practice().turns,
          { role: "candidat", text: "I am an engineer.", question: 1, relance: false, skipped: false },
          { role: "recruteur", text: "Why us?", question: 2, relance: false, skipped: false },
        ],
      }),
    });
    await wrapper.find("[data-test=practice-input]").setValue("I am an engineer.");
    await wrapper.find("[data-test=practice-input]").trigger("keydown", { key: "Enter" });
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/interview-practices/{practice_id}/answer", {
      params: { path: { practice_id: 5 } },
      body: { text: "I am an engineer." },
    });
    expect(wrapper.findAll("[data-test=practice-turn]").map((t) => t.classes("candidat"))).toEqual([false, true, false]);
    // Après une réponse, le retour peut se demander à tout moment.
    expect(wrapper.find("[data-test=practice-finish]").exists()).toBe(true);
  });

  it("sans IA : un message, pas de bouton Commencer", async () => {
    GET.mockResolvedValue({ data: { kind: "rh", language: "fr", can_practice: false } });
    const wrapper = mount(InterviewPractice, { props: {} });
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/interview-practices/defaults", { params: { query: {} } });
    expect(wrapper.text()).toContain("n'est pas configurée");
    expect(wrapper.find("[data-test=practice-start]").exists()).toBe(false);
  });

  it("le retour : repères, meilleure réponse, « Ajouter à À préparer »", async () => {
    GET.mockResolvedValue({
      data: practice({
        status: "termine",
        feedback: {
          questions: [
            { question: 1, level: "a_preciser", good: "Clair", missing: "Un chiffre", better: "I migrated…" },
          ],
          strengths: ["Structure"],
          work_on: ["Préparer un exemple chiffré"],
        },
        turns: [
          ...practice().turns,
          { role: "candidat", text: "I am an engineer.", question: 1, relance: false, skipped: false },
        ],
      }),
    });
    POST.mockResolvedValue({ data: { to_prepare: [] } });
    const wrapper = mount(InterviewPractice, { props: { practiceId: 5 } });
    await flushPromises();
    const question = wrapper.find("[data-test=practice-question]");
    expect(question.text()).toContain("1. Tell me about yourself.");
    expect(question.find("[data-test=practice-level]").text()).toBe("À préciser");
    expect(question.text()).toContain("I migrated…");
    expect(question.text()).toContain("I am an engineer.");
    await wrapper.find("[data-test=practice-add-prepare]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interviews/insights/to-prepare", {
      body: { text: "Préparer un exemple chiffré", done: false },
    });
    expect(wrapper.find("[data-test=practice-added]").text()).toBe("Ajouté à « À préparer »");
    expect(wrapper.find("[data-test=practice-added] [data-icon=done]").exists()).toBe(true);
  });

  it("dit l'erreur de l'IA et propose « Réessayer » quand le recruteur n'a pas répondu", async () => {
    GET.mockResolvedValue({
      data: practice({
        waiting: true,
        turns: [
          ...practice().turns,
          { role: "candidat", text: "Hello", question: 1, relance: false, skipped: false },
        ],
      }),
    });
    POST.mockResolvedValue({ error: { detail: "plafond mensuel de l'IA atteint" } });
    const wrapper = mount(InterviewPractice, { props: { practiceId: 5 } });
    await flushPromises();
    expect(wrapper.find("[data-test=practice-input]").exists()).toBe(false);
    await wrapper.find("[data-test=practice-retry]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Impossible : plafond mensuel de l'IA atteint.");
  });

  it("fenêtre : Échap ferme d'où qu'on soit, le focus revient au bouton d'ouverture (docs/76 §4)", async () => {
    GET.mockResolvedValue({ data: { kind: "rh", language: "fr", can_practice: true } });
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    const wrapper = mount(InterviewPractice, { props: {}, attachTo: document.body });
    await flushPromises();
    expect(document.activeElement?.getAttribute("data-test")).toBe("practice-start");
    document.body.focus();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });
});

