import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import OrpMeetingView from "./OrpMeetingView.vue";

const GET = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    POST: (...a: unknown[]) => POST(...a),
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));

const PREP = {
  summaries: ["Septembre 2026 : 12 candidatures (objectif 12).", "Octobre 2026 : 4 candidatures (objectif 12)."],
  works: null,
  blockers: ["Aucune réponse en 3 mois, sur 12 candidatures."],
  missing: [{ skill: "Terraform", count: 8, training_id: 3, training_title: "Terraform Associate" }],
  offers: 12,
  questions: [
    { key: "funding:3", text: "Est-il possible de financer la formation « Terraform Associate » ?", checked: true },
    { key: "intermediate", text: "Si je prends un emploi temporaire, comment déclarer un gain intermédiaire ?", checked: false },
  ],
  obligations: [{ text: "Preuves de septembre 2026 : à remettre au plus tard le 5 octobre.", due: "2026-10-05", done: true }],
};
const EMPTY = {
  outcome_at: null,
  agreed_target: null,
  measures: [],
  assignments: null,
  note: null,
  asked: [],
  next_starts_at: null,
  sheet_text: null,
};
const MEETING = { id: 1, starts_at: "2099-10-22T07:30:00Z", place: "ORP de Lausanne", advisor: null, ...EMPTY };
const MORE = { past: [], target: 12, trainings: [{ id: 3, title: "Terraform Associate", accepted: false }] };

beforeEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

describe("Rendez-vous ORP (docs/83)", () => {
  it("aucune candidature encore : la feuille le dit, et mène aux offres (docs/128 §3)", async () => {
    GET.mockResolvedValue({ data: { meeting: null, preparation: { ...PREP, has_applications: false }, ...MORE } });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=sheet-none-yet]").text()).toContain("Ta feuille ORP se remplit avec tes candidatures.");
    expect(wrapper.find("[data-test=sheet-summary]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
  });

  it("sans date : le formulaire, et les questions attendent la date", async () => {
    GET.mockResolvedValue({ data: { meeting: null, preparation: PREP, ...MORE } });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-blockers]").text()).toContain("Aucune réponse en 3 mois");
    expect(wrapper.find("[data-test=sheet-missing]").text()).toContain("Terraform");
    expect(wrapper.find("[data-test=sheet-missing]").text()).toContain("12 offres bien notées");
    expect(wrapper.find("[data-test='question-funding:3']").attributes("disabled")).toBeDefined();
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, ...MORE } });
    await wrapper.find("[data-test=meeting-at]").setValue("2026-10-22T09:30");
    await wrapper.find("[data-test=meeting-form]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting", {
      body: { starts_at: new Date("2026-10-22T09:30").toISOString(), place: "", advisor: "" },
    });
    expect(wrapper.find("[data-test=meeting-when]").text()).toContain("ORP de Lausanne");
  });

  it("cocher une question, en ajouter une, télécharger la feuille avec son nom", async () => {
    GET.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, ...MORE } });
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, ...MORE } });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    await wrapper.find("[data-test=question-intermediate]").setValue(true);
    await flushPromises();
    const [path, options] = PUT.mock.calls[0] as [string, { body: { questions: { key: string; checked: boolean }[] } }];
    expect(path).toBe("/api/orp-meeting/questions");
    expect(options.body.questions.find((q) => q.key === "intermediate")?.checked).toBe(true);
    await wrapper.find("[data-test=question-new]").setValue("Puis-je travailler à 80 % ?");
    await wrapper.find("[data-test=sheet-questions] form").trigger("submit");
    await flushPromises();
    const added = (PUT.mock.calls[1] as [string, { body: { questions: { text: string; checked: boolean }[] } }])[1];
    expect(added.body.questions.at(-1)).toMatchObject({ text: "Puis-je travailler à 80 % ?", checked: true });
    expect(wrapper.find("[data-test=sheet-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf");
    await wrapper.find("[data-test=sheet-download] input").setValue("Camille Exemple");
    expect(wrapper.find("[data-test=sheet-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf?name=Camille%20Exemple");
  });

  it("après le rendez-vous : noter ce qui a été convenu", async () => {
    const held = { ...MEETING, starts_at: "2020-10-22T07:30:00Z" };
    GET.mockResolvedValue({ data: { meeting: held, preparation: PREP, ...MORE } });
    const agreed = {
      ...held,
      outcome_at: "2020-10-22T09:00:00Z",
      agreed_target: 10,
      measures: [{ text: "Terraform Associate", training_id: 3 }, { text: "Cours de CV", training_id: null }],
      note: "Viser aussi l'anglais.",
    };
    PUT.mockResolvedValue({ data: { meeting: agreed, preparation: PREP, ...MORE } });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    await wrapper.find("[data-test=meeting-outcome]").trigger("click");
    expect((wrapper.find("[data-test=outcome-target]").element as HTMLInputElement).value).toBe("12");
    await wrapper.find("[data-test=outcome-target]").setValue(10);
    await wrapper.find("[data-test=outcome-training-3]").setValue(true);
    await wrapper.find("textarea").setValue("Cours de CV\n ");
    await wrapper.find("[data-test=outcome-note]").setValue("Viser aussi l'anglais.");
    await wrapper.find("[data-test=outcome-form]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/{meeting_id}/convenu", {
      params: { path: { meeting_id: 1 } },
      body: {
        target: 10,
        measures: [
          { text: "Terraform Associate", training_id: 3 },
          { text: "Cours de CV", training_id: null },
        ],
        assignments: "",
        note: "Viser aussi l'anglais.",
        next_starts_at: null,
      },
    });
    const shown = wrapper.find("[data-test=meeting-agreed]").text();
    expect(shown).toContain("10 candidatures par mois");
    expect(shown).toContain("Terraform Associate, Cours de CV");
  });

  it("le carnet, et le message rédigé par l'IA", async () => {
    const old = { ...MEETING, id: 2, starts_at: "2020-09-15T08:00:00Z", asked: ["Une mesure ?"] };
    const noted = { ...old, id: 3, asked: [], outcome_at: "2020-08-01T10:00:00Z", assignments: "Une assignation." };
    GET.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, ...MORE, past: [old, noted] } });
    POST.mockResolvedValue({
      data: { meeting: { ...MEETING, sheet_text: "Bonjour,\n\nVoici où j'en suis." }, preparation: PREP, ...MORE },
    });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    const log = wrapper.find("[data-test=meeting-log]");
    expect(log.find("[data-test=log-outcome-2]").text()).toBe("Noter ce qui a été convenu");
    expect(log.text()).toContain("Une assignation.");
    expect(log.text()).not.toContain("Une mesure ?"); // les questions, seulement une fois noté
    await wrapper.find("[data-test=sheet-write]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/orp-meeting/redaction");
    expect(wrapper.find("[data-test=sheet-text]").text()).toContain("Voici où j'en suis.");
  });
});
