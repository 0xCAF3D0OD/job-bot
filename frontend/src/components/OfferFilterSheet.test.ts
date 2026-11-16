import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, type OfferFilters } from "../composables/useOfferFilters";
import OfferFilterSheet from "./OfferFilterSheet.vue";

const facets = { sources: [{ value: "jobup", count: 3 }], cantons: [{ value: "VD", count: 2 }], scores: [], unscored: 0, sure: 104, provisional: 312 };

function mountSheet(patch: Partial<OfferFilters> = {}, total = 3) {
  return mount(OfferFilterSheet, {
    props: { open: true, filters: { ...DEFAULT_FILTERS, ...patch }, facets, total },
    global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
  });
}

describe("La feuille Filtres du téléphone (maquette Filtres, docs/139 étape 5c)", () => {
  it("note minimale sur 100, taux d’activité, tri, « Masquer les offres écartées », télétravail ; « Afficher 3 offres »", () => {
    const wrapper = mountSheet();
    // Note minimale (section 31 du 16.11) : un contrôle segmenté à 4 cases, un seul choix, titre et aide reliés.
    const scores = wrapper.find("[role=radiogroup][aria-labelledby=sheet-score-title]");
    expect(wrapper.find("#sheet-score-title").text()).toBe("Note minimale, sur 100");
    expect(scores.findAll("[role=radio]").map((b) => b.text())).toEqual(["Toutes", "50 et +", "75 et +", "85 et +"]);
    expect(scores.find("[data-test=sheet-score-all]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find(`#${scores.attributes("aria-describedby")}`).text()).toBe("À quel point l’offre correspond à ton profil.");
    // Le taux d'activité, un seul choix : un groupe de radios, pas des puces (5e), titre relié.
    const rates = wrapper.find("[role=radiogroup][aria-labelledby=sheet-rate-title]");
    expect(wrapper.find("#sheet-rate-title").text()).toBe("Taux d’activité");
    expect(rates.findAll("[role=radio]").map((b) => b.text())).toEqual(["Tous", "Dès 60 %", "Dès 80 %", "100 %"]);
    expect(rates.find("[data-test=sheet-rate-all]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=sheet-sort-day]").text()).toBe("Par date");
    expect(wrapper.find("[data-test=sheet-sort-day]").attributes("aria-pressed")).toBe("true");
    // Les écartées (Kevin, 6.11) : « Masquer », allumé par défaut, « Éteins ce réglage pour les voir dans la liste » dessous.
    const hide = wrapper.find("[data-test=sheet-filtered-out]");
    expect(hide.text()).toContain("Masquer les offres écartées");
    expect(hide.text()).toContain("Éteins ce réglage pour les voir dans la liste");
    expect((hide.find("input[role=switch]").element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find("[data-test=sheet-remote]").text()).toBe("Télétravail possible, même partiel");
    // Section 35 du 16.11 : l'interrupteur des agences, sous Télétravail.
    expect(wrapper.text()).toContain("Masquer les agences de placement");
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
    await wrapper.find("[data-test=sheet-score-all]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: null, maxScore: null }]);
    // Mêmes seuils qu'avant : 50, 75, 85 ; un seul choix marqué.
    for (const min of [50, 75, 85]) {
      const chosen = mountSheet({ minScore: min });
      expect(chosen.findAll("[data-test^=sheet-score][aria-checked=true]").map((b) => b.attributes("data-test"))).toEqual([`sheet-score-${min}`]);
    }
    expect(mountSheet({ minRate: 80 }).findAll("[data-test^=sheet-rate][aria-checked=true]").map((b) => b.text())).toEqual(["Dès 80 %"]);
    // Une adresse d'avant (?note=60-90) garde ses bornes : aucun choix marqué.
    expect(mountSheet({ minScore: 60, maxScore: 90 }).findAll("[data-test^=sheet-score][aria-checked=true]")).toHaveLength(0);
  });

  it("« Tout effacer »", async () => {
    const wrapper = mountSheet();
    expect(wrapper.find("[data-test=sheet-reset]").text()).toBe("Tout effacer");
    await wrapper.find("[data-test=sheet-reset]").trigger("click");
    expect(wrapper.emitted("reset")).toHaveLength(1);
  });

  it("groupe « Type de note » (section 31) : Toutes, Définitives · n, Provisoires · n en boutons radio, la phrase dessous, un seul choix", async () => {
    const wrapper = mountSheet();
    const group = wrapper.find("[role=radiogroup][aria-labelledby=sheet-basis-title]");
    expect(wrapper.find("#sheet-basis-title").text()).toBe("Type de note");
    expect(group.findAll("[role=radio]").map((b) => b.text())).toEqual(["Toutes", "Définitives · 104", "Provisoires · 312"]);
    expect(group.find("[data-test=sheet-basis-all]").attributes("aria-checked")).toBe("true");
    expect(group.find("[data-test=sheet-basis-all] svg").exists()).toBe(true);
    expect(group.find("[data-test=sheet-basis-sure]").attributes("aria-checked")).toBe("false");
    expect(wrapper.find(`#${group.attributes("aria-describedby")}`).text()).toBe("Provisoire : notée sur l’extrait de l’alerte, sans l’annonce complète.");
    await group.find("[data-test=sheet-basis-provisional]").trigger("click");
    expect(wrapper.emitted("update")).toEqual([[{ basis: "provisional" }]]);
    const chosen = mountSheet({ basis: "provisional" });
    expect(chosen.findAll("[role=radiogroup][aria-labelledby=sheet-basis-title] [aria-checked=true]").map((b) => b.text())).toEqual(["Provisoires · 312"]);
    // Un seul arrêt de tabulation dans le groupe : le choix coché.
    expect(chosen.findAll("[data-test^=sheet-basis][tabindex='0']")).toHaveLength(1);
  });
});
