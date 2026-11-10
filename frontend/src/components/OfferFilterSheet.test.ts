import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, type OfferFilters } from "../composables/useOfferFilters";
import OfferFilterSheet from "./OfferFilterSheet.vue";

const facets = { sources: [{ value: "jobup", count: 3 }], cantons: [{ value: "VD", count: 2 }], scores: [], unscored: 0 };

function mountSheet(patch: Partial<OfferFilters> = {}, total = 3) {
  return mount(OfferFilterSheet, {
    props: { open: true, filters: { ...DEFAULT_FILTERS, ...patch }, facets, total },
    global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
  });
}

describe("La feuille Filtres du téléphone (maquette Filtres, docs/139 étape 5c)", () => {
  it("correspondance en mots, taux minimum, tri, « Masquer les offres écartées », télétravail ; « Afficher 3 offres »", () => {
    const wrapper = mountSheet();
    expect(wrapper.findAll("[data-test^=sheet-score]").map((b) => b.text())).toEqual(["Tous", "À creuser et +", "Proche et +", "Très proche"]);
    expect(wrapper.find("[data-test=sheet-score-all]").attributes("aria-pressed")).toBe("true");
    // Le taux minimum, un seul choix : un groupe de radios, pas des puces (5e).
    const rates = wrapper.find("[role=radiogroup][aria-label='Taux minimum']");
    expect(rates.findAll("[role=radio]").map((b) => b.text())).toEqual(["Tous", "60 %", "80 %", "100 %"]);
    expect(rates.find("[data-test=sheet-rate-all]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=sheet-sort-day]").attributes("aria-pressed")).toBe("true");
    // Les écartées (Kevin, 6.11) : « Masquer », allumé par défaut, « Éteins ce réglage pour les voir dans la liste » dessous.
    const hide = wrapper.find("[data-test=sheet-filtered-out]");
    expect(hide.text()).toContain("Masquer les offres écartées");
    expect(hide.text()).toContain("Éteins ce réglage pour les voir dans la liste");
    expect((hide.find("input[role=switch]").element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find("[data-test=sheet-remote]").exists()).toBe(true);
    // Plus d'« Afficher aussi », d'expirées, de sites ni de cantons : sites et cantons se règlent dans Compte.
    for (const gone of ["sheet-show-also", "sheet-expired", "sheet-external", "sheet-doubtful", "sheet-source-jobup", "sheet-canton-VD"]) {
      expect(wrapper.find(`[data-test=${gone}]`).exists()).toBe(false);
    }
    expect(wrapper.find("[data-test^=sheet-view]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 3 offres");
    expect(mountSheet({}, 1).find("[data-test=sheet-show]").text()).toBe("Afficher 1 offre");
    // Hors d'À traiter, l'interrupteur n'a pas de sens.
    expect(mountSheet({ view: "expired" }).find("[data-test=sheet-filtered-out]").exists()).toBe(false);
  });

  it("chaque choix s’applique tout de suite", async () => {
    const wrapper = mountSheet();
    await wrapper.find("[data-test=sheet-score-50]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: 50, maxScore: null }]);
    await wrapper.find("[data-test=sheet-rate-80]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 80 }]);
    await wrapper.find("[data-test=sheet-sort-score]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ sort: "score" }]);
    // Éteindre « Masquer » montre les écartées.
    await wrapper.find("[data-test=sheet-filtered-out] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ showFilteredOut: true }]);
    expect((mountSheet({ showFilteredOut: true }).find("[data-test=sheet-filtered-out] input").element as HTMLInputElement).checked).toBe(false);
    await wrapper.find("[data-test=sheet-remote] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ remote: "partial" }]);
    await wrapper.find("[data-test=sheet-rate-all]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: null }]);
    expect(mountSheet({ minScore: 75 }).find("[data-test=sheet-score-75]").attributes("aria-pressed")).toBe("true");
    // Une adresse d'avant (?note=60-90) garde ses bornes : aucun choix marqué.
    expect(mountSheet({ minScore: 60, maxScore: 90 }).findAll("[data-test^=sheet-score][aria-pressed=true]")).toHaveLength(0);
  });

  it("« Tout effacer »", async () => {
    const wrapper = mountSheet();
    expect(wrapper.find("[data-test=sheet-reset]").text()).toBe("Tout effacer");
    await wrapper.find("[data-test=sheet-reset]").trigger("click");
    expect(wrapper.emitted("reset")).toHaveLength(1);
  });
});
