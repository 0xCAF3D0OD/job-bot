import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import OrpMeetingView from "./OrpMeetingView.vue";

const GET = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
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
const MEETING = { id: 1, starts_at: "2026-10-22T07:30:00Z", place: "ORP de Lausanne", advisor: null };

beforeEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

describe("Rendez-vous ORP (docs/83)", () => {
  it("sans date : le formulaire, et les questions attendent la date", async () => {
    GET.mockResolvedValue({ data: { meeting: null, preparation: PREP } });
    const wrapper = mount(OrpMeetingView, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-blockers]").text()).toContain("Aucune réponse en 3 mois");
    expect(wrapper.find("[data-test=sheet-missing]").text()).toContain("Terraform");
    expect(wrapper.find("[data-test=sheet-missing]").text()).toContain("12 offres bien notées");
    expect(wrapper.find("[data-test='question-funding:3']").attributes("disabled")).toBeDefined();
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP } });
    await wrapper.find("[data-test=meeting-at]").setValue("2026-10-22T09:30");
    await wrapper.find("[data-test=meeting-form]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting", {
      body: { starts_at: new Date("2026-10-22T09:30").toISOString(), place: "", advisor: "" },
    });
    expect(wrapper.find("[data-test=meeting-when]").text()).toContain("ORP de Lausanne");
  });

  it("cocher une question, en ajouter une, télécharger la feuille avec son nom", async () => {
    GET.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP } });
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP } });
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
});
