import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CriteriaView from "./CriteriaView.vue";

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
