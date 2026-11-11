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
      Promise.resolve({ data: { criteria: body, keywords, returned: 112 }, response: { status: 200 } }),
    );
    const wrapper = mount(CriteriaView);
    await flushPromises();

    expect(wrapper.text()).toContain("VD");
    // La description en une ligne sous son titre, les mots-clés au survol (docs/110, docs/118 §1).
    const descriptions = wrapper.findAll(".setting-desc").map((p) => p.text());
    expect(descriptions).toContain("Écartée si le titre ou l’extrait contient un mot du type.");
    const notes = wrapper.findAllComponents(HoverNote).map((n) => n.props("text"));
    expect(notes.some((t) => t.includes("Stages\u202f: stage, internship…"))).toBe(true);

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
    expect(wrapper.find("[role=status]").text()).toBe("Critères enregistrés. 112 offres reviennent dans À examiner.");
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
          language_levels: { francais: "native", allemand: "notions" },
        },
        keywords: { contract_types: {}, language_names: {}, requirement_words: [] },
        saved_at: "2026-10-01T08:00:00Z",
      },
    });
    const wrapper = mount(CriteriaView);
    await flushPromises();
    const summary = wrapper.find("[data-test=criteria-summary]");
    // Une ligne cliquable par critère, le libellé au-dessus de la valeur (lot 13.2) ; cantons en toutes lettres
    // (docs/43 n° 23, 24).
    const rows = summary
      .findAll("button.criteria-row")
      .map((row) => [row.find(".criteria-row-label").text(), row.find(".criteria-row-value").text()]);
    expect(rows).toEqual([
      ["Lieux", "Vaud, Genève"],
      ["Télétravail complet", "Accepté s’il est ouvert depuis la Suisse"],
      ["Taux d’activité", "80 % au moins"],
      ["Types d’offres exclus", "Stages"],
      // « Langues » avec les niveaux (PR 17), plus « Langues non parlées ».
      ["Langues", "Français\u202f: langue maternelle, Allemand\u202f: notions"],
      ["Suivi ORP", "Non renseigné"],
    ]);
    // À droite, le cercle D29 de 36 px (décoratif), plus de chevron gris.
    for (const row of summary.findAll("button.criteria-row")) {
      expect(row.find(".arrow-circle.small").attributes("aria-hidden")).toBe("true");
    }
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(false);
    await wrapper.find("[data-test=criteria-row-taux]").trigger("click");
    await flushPromises();
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

  it("taux hors limites : l’erreur sous le champ, pas d’enregistrement", async () => {
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

  it("les lignes de ProfilOrdinateur ; toucher une ligne ouvre le formulaire sur ce critère", async () => {
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
                  { rule: "type", label: "Type d’offre", count: 1 },
                  { rule: "lieu", label: "Lieu", count: 1 },
                  { rule: "taux", label: "Taux d’activité", count: 1 },
                ],
              },
            },
      ),
    );
    const wrapper = mount(CriteriaView, { attachTo: document.body });
    await flushPromises();

    // Prompt du 10 novembre (PR 20, point 5) : le format de ProfilOrdinateur aussi sur téléphone, libellé gris au-dessus
    // de la valeur en gras, cercle à flèche.
    const summary = wrapper.find("[data-test=criteria-summary]");
    const labels = summary.findAll(".criteria-row-label").map((t) => t.text());
    expect(labels).toEqual(["Lieux", "Télétravail complet", "Taux d’activité", "Types d’offres exclus", "Langues", "Suivi ORP"]);
    expect(summary.find("[data-test=criteria-row-taux] .criteria-row-value").text()).toBe("80 % au moins");
    expect(summary.find(".grouped-value").exists()).toBe(false);

    // « Écartées surtout pour » : une ligne par raison.
    const outcome = wrapper.find("[data-test=filter-outcome]");
    expect(outcome.findAll("[data-test=filter-reasons] .criteria-row-value").map((t) => t.text())).toEqual([
      "1 offre pour : Type d’offre",
      "1 offre pour : Lieu",
      "1 offre pour : Taux d’activité",
    ].map((t) => t.replace(" :", "\u202f:")));

    await wrapper.find("button[data-test=criteria-row-taux]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(true);
    expect(document.activeElement?.id).toBe("min_rate");
    wrapper.unmount();
  });

  it("« Suivi ORP » en dernière ligne : l’objectif, qui ouvre « Objectif du mois » et suit l’enregistrement (PR 50)", async () => {
    const settings = { orp_monthly_target: 10, orp_due_day: 5 };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/settings" ? settings : { criteria: { locations: ["VD"], min_rate: null }, keywords, saved_at: "2026-11-01T08:00:00Z" } }),
    );
    PUT.mockImplementation((_path: string, { body }: { body: unknown }) => Promise.resolve({ data: body }));
    const wrapper = mount(CriteriaView, { attachTo: document.body });
    await flushPromises();
    const rows = wrapper.findAll("[data-test=criteria-summary] .criteria-row");
    const row = rows[rows.length - 1]!;
    expect(row.attributes("data-test")).toBe("criteria-row-orp");
    expect(row.find(".criteria-row-label").text()).toBe("Suivi ORP");
    expect(row.find(".criteria-row-value").text()).toBe("10 recherches par mois");
    expect(rows[rows.length - 2]!.find(".criteria-row-label").text()).toBe("Langues");

    await row.trigger("click");
    expect(wrapper.find("[data-test=goal-sheet]").attributes("open")).toBeDefined();
    expect(wrapper.find("[data-test=criteria-form]").exists()).toBe(false);
    await wrapper.find("[data-test=goal-more]").trigger("click");
    await wrapper.find("[data-test=goal-more]").trigger("click");
    await wrapper.find("[data-test=goal-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/settings", { body: { ...settings, orp_monthly_target: 12 } });
    expect(wrapper.find("[data-test=criteria-row-orp] .criteria-row-value").text()).toBe("12 recherches par mois");
    expect(wrapper.find("[data-test=goal-sheet]").attributes("open")).toBeUndefined();
    wrapper.unmount();
  });

  it("sans objectif : « Non renseigné »", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/settings" ? { orp_monthly_target: null } : { criteria: { locations: ["VD"], min_rate: null }, keywords, saved_at: "2026-11-01T08:00:00Z" } }),
    );
    const wrapper = mount(CriteriaView);
    await flushPromises();
    expect(wrapper.find("[data-test=criteria-row-orp] .criteria-row-value").text()).toBe("Non renseigné");
  });
});
