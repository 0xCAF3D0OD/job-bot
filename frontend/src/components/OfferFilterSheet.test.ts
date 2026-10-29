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

describe("OfferFilterSheet (planche « Structure téléphone », 248:306)", () => {
  it("statut et note minimale en radios, télétravail en interrupteur, « Afficher 3 offres »", () => {
    const wrapper = mountSheet();
    expect(wrapper.find("[data-test=sheet-view-to_review] input[type=radio]").element).toHaveProperty("checked", true);
    expect(wrapper.findAll("[data-test^=sheet-score] input[type=radio]")).toHaveLength(3);
    expect(wrapper.find("[data-test=sheet-score-all] input").element).toHaveProperty("checked", true);
    expect(wrapper.find("[data-test=sheet-remote] input[role=switch]").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 3 offres");
    expect(mountSheet({}, 1).find("[data-test=sheet-show]").text()).toBe("Afficher 1 offre");
  });

  it("la note minimale : les mêmes choix que sur ordinateur, ligne entière cliquable", async () => {
    const wrapper = mountSheet();
    expect(wrapper.findAll("[data-test^=sheet-score]").map((row) => row.text())).toEqual(["Toutes", "Proche et plus", "Très proche"]);
    await wrapper.find("[data-test=sheet-score-85] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: 85, maxScore: null }]);
    await wrapper.find("[data-test=sheet-score-all] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: null, maxScore: null }]);
    expect(mountSheet({ minScore: 70 }).find("[data-test=sheet-score-70] input").element).toHaveProperty("checked", true);
    // Une adresse d'avant (?note=60-90) garde ses bornes : aucune radio cochée.
    const old = mountSheet({ minScore: 60, maxScore: 90 });
    expect(old.findAll("[data-test^=sheet-score] input:checked")).toHaveLength(0);
  });

  it("taux, sites, cantons et réinitialiser", async () => {
    const wrapper = mountSheet();
    await wrapper.find("[data-test=sheet-rate] select").setValue("80");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 80 }]);
    await wrapper.find("[data-test=sheet-source-jobup] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ sources: ["jobup"] }]);
    await wrapper.find("[data-test=sheet-canton-VD] input").trigger("change");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ cantons: ["VD"] }]);
    await wrapper.find("[data-test=sheet-reset]").trigger("click");
    expect(wrapper.emitted("reset")).toHaveLength(1);
  });
});
