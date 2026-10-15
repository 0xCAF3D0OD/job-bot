import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CriteriaView from "./CriteriaForm.vue";
import HoverNote from "./HoverNote.vue";

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
    // Description au survol du libellé (docs/53), plus de « ? ».
    const typesNote = wrapper.findAllComponents(HoverNote).find((h) => h.text().includes("Types d'offres exclus"));
    expect(typesNote?.props("text")).toContain("Stages : stage, internship…");

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
    expect(wrapper.find(".form-actions [role=status]").text()).toContain("refiltrées");
  });
});

describe("CriteriaForm, déjà saisis", () => {
  it("montre un résumé, puis le formulaire pré-rempli sur « Modifier »", async () => {
    GET.mockResolvedValue({
      data: {
        criteria: {
          locations: ["VD", "Genève"],
          remote_policy: "from_switzerland",
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
    // Lignes alignées, cantons en toutes lettres (docs/43 n° 23, 24).
    const rows = summary.findAll(".summary-rows > div").map((row) => [row.find("dt").text(), row.find("dd").text()]);
    expect(rows).toEqual([
      ["Lieux", "Vaud, Genève"],
      ["Télétravail complet", "accepté s'il est ouvert depuis la Suisse"],
      ["Taux d'activité", "80 % au moins"],
      ["Types d'offres exclus", "stages"],
    ]);
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(false);
    await wrapper.find("[data-test=edit-criteria]").trigger("click");
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=cancel-criteria]").exists()).toBe(true);
  });
});
