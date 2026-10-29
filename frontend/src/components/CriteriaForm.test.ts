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
    // La description en une ligne sous son titre, les mots-clés au survol (docs/110, docs/118 §1).
    const descriptions = wrapper.findAll(".setting-desc").map((p) => p.text());
    expect(descriptions).toContain("Écartée si le titre ou l'extrait contient un mot du type.");
    const notes = wrapper.findAllComponents(HoverNote).map((n) => n.props("text"));
    expect(notes.some((t) => t.includes("Stages : stage, internship…"))).toBe(true);

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

describe("CriteriaForm, chargement et erreurs (règles §4)", () => {
  it("des blocs gris tant que les critères chargent, pas un formulaire vide", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    const wrapper = mount(CriteriaView);
    await flushPromises();
    expect(wrapper.find("[data-test=loading]").exists()).toBe(true);
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(false);
    expect(wrapper.find("[data-test=criteria-missing]").exists()).toBe(false);
  });

  it("taux hors limites : l'erreur sous le champ, pas d'enregistrement", async () => {
    GET.mockResolvedValue({ data: { criteria: { locations: ["VD"], min_rate: null }, keywords } });
    const wrapper = mount(CriteriaView, { attachTo: document.body });
    await flushPromises();
    const rate = wrapper.find("[data-test=criteria-min-rate]");
    await rate.setValue("150");
    await rate.trigger("blur");
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Indique un taux entier de 1 à 100, ou laisse vide.");
    expect(rate.attributes("aria-invalid")).toBe("true");
    await wrapper.find("[data-test=criteria-form]").trigger("submit");
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(rate.element);
    await rate.setValue("80");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    wrapper.unmount();
  });
});

describe("CriteriaView sous 600 px (planche « Structure téléphone »)", () => {
  const original = globalThis.matchMedia;
  afterEach(() => {
    globalThis.matchMedia = original;
  });

  it("le résumé en liste groupée ; toucher une ligne ouvre le formulaire sur ce critère", async () => {
    globalThis.matchMedia = ((query: string) =>
      ({ matches: query.includes("599px"), addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList);
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/criteria"
          ? {
              data: {
                criteria: { locations: ["VD"], min_rate: 80, excluded_types: ["stage", "temporaire"] },
                keywords,
                saved_at: "2026-10-20T10:00:00Z",
              },
            }
          : {
              data: {
                received: 36,
                retained: 33,
                reasons: [
                  { rule: "type", label: "Type d'offre", count: 1 },
                  { rule: "lieu", label: "Lieu", count: 1 },
                  { rule: "taux", label: "Taux d'activité", count: 1 },
                ],
              },
            },
      ),
    );
    const wrapper = mount(CriteriaView, { attachTo: document.body });
    await flushPromises();

    const summary = wrapper.find("[data-test=criteria-summary]");
    expect(summary.find(".grouped-title").text()).toBe("Poste recherché");
    const titles = summary.findAll(".grouped-row-title").map((t) => t.text());
    expect(titles).toEqual(["Lieux", "Télétravail complet", "Taux d'activité", "Types d'offres exclus"]);
    expect(summary.find("[data-test=criteria-row-taux] .grouped-row-description").text()).toBe("80 % au moins");

    const outcome = wrapper.find("[data-test=filter-outcome]");
    expect(outcome.findAll(".grouped-row-title").map((t) => t.text())).toEqual([
      "33 offres passent sur 36",
      "Écartées surtout pour",
    ]);
    expect(outcome.text()).toContain("Type d'offre, lieu, taux d'activité : 1 chacune.");

    await wrapper.find("[data-test=criteria-row-taux] button").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(true);
    expect(document.activeElement?.id).toBe("min_rate");
    wrapper.unmount();
  });
});
