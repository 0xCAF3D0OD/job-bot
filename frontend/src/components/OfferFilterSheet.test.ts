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
  it("correspondance en mots, taux, tri, « Masquer les offres écartées » ; « Afficher 3 offres »", () => {
    const wrapper = mountSheet();
    expect(wrapper.findAll("[data-test^=sheet-score]").map((b) => b.text())).toEqual(["Tous", "À creuser et +", "Proche et +", "Très proche"]);
    expect(wrapper.find("[data-test=sheet-score-all]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.findAll("[data-test^=sheet-rate]").map((b) => b.text())).toEqual(["Tous", "60 % et +", "80 % et +", "100 %"]);
    expect(wrapper.find("[data-test=sheet-sort-day]").attributes("aria-pressed")).toBe("true");
    // Les écartées sont masquées par défaut : l'interrupteur est allumé.
    expect(wrapper.find("[data-test=sheet-filtered-out] input[role=switch]").element).toHaveProperty("checked", true);
    expect(wrapper.find("[data-test^=sheet-view]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 3 offres");
    expect(mountSheet({}, 1).find("[data-test=sheet-show]").text()).toBe("Afficher 1 offre");
    // Hors d'À traiter, l'interrupteur n'a pas de sens.
    expect(mountSheet({ view: "expired" }).find("[data-test=sheet-filtered-out]").exists()).toBe(false);
  });

  it("chaque choix s'applique tout de suite", async () => {
    const wrapper = mountSheet();
    await wrapper.find("[data-test=sheet-score-50]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: 50, maxScore: null }]);
    await wrapper.find("[data-test=sheet-rate-80]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 80 }]);
    await wrapper.find("[data-test=sheet-sort-score]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ sort: "score" }]);
    await wrapper.find("[data-test=sheet-filtered-out] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ showFilteredOut: true }]);
    expect(mountSheet({ minScore: 70 }).find("[data-test=sheet-score-70]").attributes("aria-pressed")).toBe("true");
    // Une adresse d'avant (?note=60-90) garde ses bornes : aucun choix marqué.
    expect(mountSheet({ minScore: 60, maxScore: 90 }).findAll("[data-test^=sheet-score][aria-pressed=true]")).toHaveLength(0);
  });

  it("sites, cantons et « Tout effacer »", async () => {
    const wrapper = mountSheet();
    await wrapper.find("[data-test=sheet-source-jobup] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ sources: ["jobup"] }]);
    await wrapper.find("[data-test=sheet-canton-VD] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ cantons: ["VD"] }]);
    expect(wrapper.find("[data-test=sheet-reset]").text()).toBe("Tout effacer");
    await wrapper.find("[data-test=sheet-reset]").trigger("click");
    expect(wrapper.emitted("reset")).toHaveLength(1);
  });
});
