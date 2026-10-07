import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ApplicationCard from "./ApplicationCard.vue";
import InterviewForm from "./InterviewForm.vue";

describe("InterviewForm (docs/23 §2)", () => {
  it("ressenti obligatoire, questions proposées, réponse salaire, suite datée", async () => {
    const wrapper = mount(InterviewForm, {
      props: { company: "Exemple SA", initial: null, heldAt: "2026-10-06", withEmployerFeedback: false, error: "" },
    });
    expect(wrapper.find("[data-test=save-interview]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=kind-technique]").trigger("click");
    await wrapper.find("[data-test=rating-4]").trigger("click");
    await wrapper.findAll("[data-test=suggested-question]")[1]!.trigger("click"); // « Pourquoi ce poste ? »
    await wrapper.find("[data-test=new-question]").setValue("Kubernetes en production");
    await wrapper.find("[data-test=new-question]").trigger("keydown", { key: "Enter" });
    const questions = wrapper.findAll("[data-test=interview-question]");
    expect(questions).toHaveLength(2);
    await questions[1]!.find("input").setValue(true);
    await wrapper.find("[data-test=salary-yes]").trigger("click");
    await wrapper.find("input[aria-label='Ce que tu as répondu']").setValue("95 000 CHF");
    await wrapper.find("[data-test=went-well]").setValue("Démo réussie");
    await wrapper.find("[data-test=next-step]").setValue("reponse");
    await wrapper.find("[data-test=next-step-at]").setValue("2026-10-20");
    await wrapper.find("[data-test=interview-form]").trigger("submit");
    const [value] = wrapper.emitted("submit")![0] as [Record<string, unknown>];
    expect(value).toMatchObject({
      kind: "technique",
      held_at: "2026-10-06",
      rating: 4,
      questions: [
        { text: "Pourquoi ce poste ?", difficult: false },
        { text: "Kubernetes en production", difficult: true },
      ],
      salary_asked: true,
      salary_answer: "95 000 CHF",
      went_well: "Démo réussie",
      went_badly: null,
      next_step: "reponse",
      next_step_at: "2026-10-20",
    });
  });
});

const application = {
  id: 3,
  offer_id: null,
  sent_at: "2026-10-02",
  method: "electronique",
  assigned_by_orp: false,
  company: "Exemple SA",
  job_title: "Ingénieur DevOps",
  status: "entretien",
  interview_at: "2026-10-06T09:00:00Z",
  orp_month: "2026-10",
  reminded_at: null,
  created_at: "2026-10-02T10:00:00Z",
  letter_draft_id: null,
  cv_draft_id: null,
};

describe("ApplicationCard, retour d'entretien (docs/23 §3)", () => {
  it("entretien passé sans retour : « Faire le point »", async () => {
    const wrapper = mount(ApplicationCard, { props: { application: { ...application, interviews: [] } as never } });
    await wrapper.find("[data-test=interview-feedback]").trigger("click");
    expect(wrapper.emitted("interview")![0]).toEqual([expect.objectContaining({ id: 3 }), null]);
  });

  it("retour fait : résumé d'une ligne et « Voir le retour »", () => {
    const interview = { id: 9, application_id: 3, kind: "technique", held_at: "2026-10-06", rating: 4, next_step: "reponse", next_step_at: "2026-10-20" };
    const wrapper = mount(ApplicationCard, { props: { application: { ...application, interviews: [interview] } as never } });
    expect(wrapper.find("[data-test=interview-summary]").text()).toBe("Technique · ressenti 4/5 · suite : une réponse attendue avant le 20.10.2026");
    expect(wrapper.find("[data-test=interview-feedback]").exists()).toBe(false);
    expect(wrapper.find("[data-test=interview-open]").exists()).toBe(true);
  });
});
