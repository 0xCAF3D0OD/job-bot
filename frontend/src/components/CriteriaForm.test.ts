import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CriteriaView from "./CriteriaForm.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...args: unknown[]) => GET(...args),
    PUT: (...args: unknown[]) => PUT(...args),
  },
}));

afterEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

const keywords = {
  contract_types: { stage: ["stage", "internship"], apprentissage: [], temporaire: [], freelance: [] },
  language_names: { allemand: ["allemand"], italien: [], anglais: [] },
  requirement_words: ["courant", "fluent"],
};

describe("CriteriaView", () => {
  it("charge, modifie et enregistre les prérequis", async () => {
    GET.mockResolvedValue({ data: { criteria: { locations: ["VD"], min_rate: null }, keywords } });
    PUT.mockImplementation((_path: string, { body }: { body: unknown }) =>
      Promise.resolve({ data: { criteria: body, keywords }, response: { status: 200 } }),
    );
    const wrapper = mount(CriteriaView);
    await flushPromises();

    expect(wrapper.text()).toContain("VD");
    expect(wrapper.text()).toContain("Cherche : stage, internship");

    const locationInput = wrapper.find("#locations");
    await locationInput.setValue("Genève");
    await locationInput.trigger("keydown.enter");
    await wrapper.find("#min_rate").setValue("80");
    await wrapper.find("input[value=stage]").setValue(true);
    await wrapper.find("[data-test=criteria-form]").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/api/criteria", {
      body: expect.objectContaining({
        locations: ["VD", "Genève"],
        min_rate: 80,
        excluded_types: ["stage"],
      }),
    });
    expect(wrapper.find("[role=status]").text()).toContain("refiltrées");
  });
});

describe("CriteriaForm, déjà saisis", () => {
  it("montre un résumé, puis le formulaire pré-rempli sur « Modifier »", async () => {
    GET.mockResolvedValue({
      data: {
        criteria: {
          locations: ["VD", "Genève"],
          remote_ok: true,
          min_rate: 80,
          excluded_types: ["stage"],
          banned_words: [],
          unspoken_languages: [],
        },
        keywords: { contract_types: {}, language_names: {}, requirement_words: [] },
        saved_at: "2026-10-01T08:00:00Z",
      },
    });
    const wrapper = mount(CriteriaView);
    await flushPromises();
    const summary = wrapper.find("[data-test=criteria-summary]");
    expect(summary.text()).toContain("Lieux : VD, Genève, ou télétravail complet");
    expect(summary.text()).toContain("80 % au moins");
    expect(summary.text()).toContain("Exclus : stages");
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(false);
    await wrapper.find("[data-test=edit-criteria]").trigger("click");
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=cancel-criteria]").exists()).toBe(true);
  });
});
