import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, type OfferFilters } from "../composables/useOfferFilters";
import OfferFilterSheet from "./OfferFilterSheet.vue";

// 20 tranches de 5 points : 10 offres de 0 à 49, 50 de 50 à 74, 13 de 75 à 84, 8 de 85 à 100 ; 3 sans note.
const scores = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 10, 10, 10, 10, 6, 7, 2, 3, 3];
const rates = [{ value: "all", count: 84 }, { value: "60", count: 72 }, { value: "80", count: 60 }, { value: "100", count: 33 }];
const facets = { sources: [{ value: "jobup", count: 3 }], cantons: [{ value: "VD", count: 2 }], scores, unscored: 3, sure: 104, provisional: 312, rates, contracts: [], distances: [] };

const counts = { pending: 38, to_review: 12, later: 4, in_progress: 2, filtered_out: 3, expired: 1, all: 50 };

function mountSheet(patch: Partial<OfferFilters> = {}, total = 3) {
  return mount(OfferFilterSheet, {
    props: { open: true, filters: { ...DEFAULT_FILTERS, ...patch }, facets, total, counts },
    global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
  });
}

describe("La feuille Filtres du téléphone (maquette Filtres, docs/139 étape 5c)", () => {
  it("note minimale sur 100, taux d’activité, tri, « Masquer les offres écartées », télétravail ; « Afficher 3 offres »", () => {
    const wrapper = mountSheet();
    // Note minimale (section 31 du 16.11) : un contrôle segmenté à 4 cases, un seul choix, titre et aide reliés.
    const scores = wrapper.find("[role=radiogroup][aria-labelledby=sheet-score-title]");
    expect(wrapper.find("#sheet-score-title").text()).toBe("Note minimale, sur 100");
    expect(scores.findAll("[role=radio] .segmented-label").map((b) => b.text())).toEqual(["Toutes", "50 et +", "75 et +", "85 et +"]);
    expect(scores.find("[data-test=sheet-score-all]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find(`#${scores.attributes("aria-describedby")}`).text()).toBe("À quel point l’offre correspond à ton profil");
    // Le taux d'activité, un seul choix : un groupe de radios, pas des puces (5e), titre relié.
    const rates = wrapper.find("[role=radiogroup][aria-labelledby=sheet-rate-title]");
    expect(wrapper.find("#sheet-rate-title").text()).toBe("Taux d’activité");
    expect(rates.findAll("[role=radio] .segmented-label").map((b) => b.text())).toEqual(["Tous", "Dès 60 %", "Dès 80 %", "100 %"]);
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
    // « Statut » en tête (Kevin, 17.11) : fieldset et légende, un seul choix, les nombres de l'ordinateur.
    const status = wrapper.find("fieldset.filter-status");
    expect(status.find("legend").text()).toBe("Statut");
    expect(wrapper.find(".filter-sheet > *").element).toBe(status.element);
    const views = status.find("[role=radiogroup][aria-labelledby=sheet-view-title]");
    expect(views.findAll("[role=radio]").map((b) => b.text())).toEqual(["Toutes · 38", "Nouvelles · 12", "Gardées · 4", "En préparation · 2"]);
    expect(views.find("[data-test=sheet-view-pending]").attributes("aria-checked")).toBe("true");
    expect(views.find("[data-test=sheet-view-pending] .icon-tick").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 3 offres");
    expect(mountSheet({}, 1).find("[data-test=sheet-show]").text()).toBe("Afficher 1 offre");
    // Hors d'À traiter, l'interrupteur n'a pas de sens.
    expect(mountSheet({ view: "expired" }).find("[data-test=sheet-filtered-out]").exists()).toBe(false);
  });

  it("§65 : le nombre d'offres sous chaque choix de Note et de Taux, le choix actif égal à « Afficher n offres »", () => {
    const counts = (wrapper: ReturnType<typeof mountSheet>, title: string) =>
      wrapper.find(`[role=radiogroup][aria-labelledby=${title}]`).findAll(".segmented-sub").map((s) => s.text());
    const all = mountSheet({}, 84);
    expect(counts(all, "sheet-score-title")).toEqual(["84", "71", "21", "8"]);
    expect(counts(all, "sheet-rate-title")).toEqual(["84", "72", "60", "33"]);
    // Le choix actif : le même nombre que le bouton (le serveur compte avec les mêmes filtres).
    const close = mountSheet({ minScore: 75 }, 21);
    const active = close.find("[data-test=sheet-score-75]");
    expect(active.attributes("aria-checked")).toBe("true");
    expect(active.find(".segmented-sub").text()).toBe("21");
    expect(close.find("[data-test=sheet-show]").text()).toBe("Afficher 21 offres");
  });

  it("Contrat : plusieurs choix, « CDI · 120 », « Non précisé » compris, un choix à 0 grisé mais cliquable", async () => {
    const contracts = [
      { value: "cdi", count: 120 },
      { value: "cdd", count: 14 },
      { value: "stage", count: 0 },
      { value: "temporaire", count: 3 },
      { value: "non_precise", count: 41 },
    ];
    const wrapper = mount(OfferFilterSheet, {
      props: { open: true, filters: { ...DEFAULT_FILTERS, contracts: ["cdi"] }, facets: { ...facets, contracts }, total: 120, counts },
      global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
    });
    const buttons = wrapper.findAll("[data-test^=sheet-contract-]");
    expect(buttons.map((b) => b.text())).toEqual(["CDI · 120", "CDD · 14", "Stage · 0", "Temporaire · 3", "Non précisé · 41"]);
    expect(wrapper.find("#sheet-contract-title").text()).toBe("Contrat");
    expect(wrapper.find("[data-test=sheet-contract-cdi]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=sheet-contract-cdi] .icon-tick").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-contract-stage]").classes()).toContain("choice-empty");
    expect(wrapper.find("[data-test=sheet-contract-stage]").attributes("disabled")).toBeUndefined();
    // Le contrat coché égale « Afficher n offres ».
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 120 offres");
    await wrapper.find("[data-test=sheet-contract-non_precise]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ contracts: ["cdi", "non_precise"] }]);
    await wrapper.find("[data-test=sheet-contract-cdi]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ contracts: [] }]);
  });

  it("« Distance depuis Renens » : un seul choix, le nombre sous chaque choix, « Lieu non précisé » avec le sien (issue 468)", async () => {
    const distances = [
      { value: "all", count: 84 },
      { value: "15", count: 12 },
      { value: "30", count: 31 },
      { value: "50", count: 0 },
      { value: "unknown", count: 9 },
    ];
    // Sans commune connue, pas de groupe.
    expect(mountSheet().find("#sheet-distance-title").exists()).toBe(false);
    const wrapper = mount(OfferFilterSheet, {
      props: { open: true, filters: { ...DEFAULT_FILTERS, distance: "30" }, facets: { ...facets, distances, distance_from: "Renens" }, total: 31, counts },
      global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
    });
    expect(wrapper.find("#sheet-distance-title").text()).toBe("Distance depuis Renens");
    const group = wrapper.find("[role=radiogroup][aria-labelledby=sheet-distance-title]");
    expect(group.findAll("[role=radio]").map((b) => b.text())).toEqual(["Toutes84", "15 km12", "30 km31", "50 km0"]);
    // Le choix actif égale « Afficher n offres ».
    expect(group.find("[data-test=sheet-distance-30]").attributes("aria-checked")).toBe("true");
    expect(group.find("[data-test=sheet-distance-30] .segmented-sub").text()).toBe("31");
    expect(wrapper.find("[data-test=sheet-show]").text()).toBe("Afficher 31 offres");
    expect(group.find("[data-test=sheet-distance-50]").classes()).toContain("choice-empty");
    const unknown = wrapper.find("[data-test=sheet-distance-unknown]");
    expect(unknown.text()).toBe("Lieu non précisé · 9");
    expect(unknown.attributes("aria-pressed")).toBe("false");
    await unknown.trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ distance: "unknown" }]);
    await group.find("[data-test=sheet-distance-all]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ distance: null }]);
  it("offres « Loin » cachées ou non : le nombre du choix actif égale toujours « Afficher n offres » (Kevin, 18.11, choix a)", () => {
    // 84 offres dont 10 « Loin » (sous 50) : la liste du téléphone les cache, le bouton dit 74.
    const near = {
      views: [{ value: "pending", count: 74 }, { value: "to_review", count: 9 }, { value: "later", count: 4 }, { value: "in_progress", count: 2 }],
      sure: 70,
      provisional: 1,
      rates: [{ value: "all", count: 74 }, { value: "60", count: 63 }, { value: "80", count: 52 }, { value: "100", count: 30 }],
      contracts: [{ value: "cdi", count: 60 }, { value: "cdd", count: 0 }, { value: "stage", count: 0 }, { value: "temporaire", count: 0 }, { value: "non_precise", count: 14 }],
      distances: [{ value: "all", count: 74 }, { value: "15", count: 20 }, { value: "30", count: 40 }, { value: "50", count: 60 }, { value: "unknown", count: 6 }],
    };
    const props = (far: number, total: number) => ({
      open: true,
      filters: DEFAULT_FILTERS,
      facets: {
        ...facets,
        contracts: [{ value: "cdi", count: 64 }, { value: "non_precise", count: 20 }],
        distance_from: "Renens",
        distances: [{ value: "all", count: 84 }, { value: "15", count: 22 }, { value: "30", count: 44 }, { value: "50", count: 66 }, { value: "unknown", count: 8 }],
        near,
      },
      total,
      counts: { ...counts, pending: 84 },
      far,
    });
    const stubs = { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } };
    const active = (wrapper: ReturnType<typeof mountSheet>) => ({
      view: wrapper.find("[data-test=sheet-view-pending]").text(),
      score: wrapper.find("[data-test=sheet-score-all] .segmented-sub").text(),
      rate: wrapper.find("[data-test=sheet-rate-all] .segmented-sub").text(),
      button: wrapper.find("[data-test=sheet-show]").text(),
      contract: wrapper.find("[data-test=sheet-contract-non_precise]").text(),
      distance: wrapper.find("[data-test=sheet-distance-all] .segmented-sub").text(),
      unknown: wrapper.find("[data-test=sheet-distance-unknown]").text(),
    });
    // Cachées : 74 partout.
    expect(active(mount(OfferFilterSheet, { props: props(10, 74), global: { stubs } }))).toEqual({
      view: "Toutes · 74",
      score: "74",
      rate: "74",
      button: "Afficher 74 offres",
      contract: "Non précisé · 14",
      distance: "74",
      unknown: "Lieu non précisé · 6",
    });
    // Montrées (ou aucune offre « Loin ») : 84 partout.
    expect(active(mount(OfferFilterSheet, { props: props(0, 84), global: { stubs } }))).toEqual({
      view: "Toutes · 84",
      score: "84",
      rate: "84",
      button: "Afficher 84 offres",
      contract: "Non précisé · 20",
      distance: "84",
      unknown: "Lieu non précisé · 8",
    });
  });

  it("un choix à 0 offre reste visible et cliquable, grisé (Kevin, 18.11)", async () => {
    const wrapper = mount(OfferFilterSheet, {
      props: {
        open: true,
        filters: DEFAULT_FILTERS,
        facets: { ...facets, sure: 0, rates: [{ value: "all", count: 84 }, { value: "60", count: 0 }, { value: "80", count: 0 }, { value: "100", count: 0 }] },
        total: 84,
        counts: { pending: 84, to_review: 0, filtered_out: 0, later: 3, in_progress: 1, expired: 0, all: 0 },
      },
      global: { stubs: { BottomSheet: { template: "<div><slot /><slot name='actions' /></div>" } } },
    });
    for (const test of ["sheet-rate-60", "sheet-view-to_review", "sheet-basis-sure"]) expect(wrapper.find(`[data-test=${test}]`).classes()).toContain("choice-empty");
    for (const test of ["sheet-rate-all", "sheet-view-later", "sheet-basis-provisional"]) expect(wrapper.find(`[data-test=${test}]`).classes()).not.toContain("choice-empty");
    await wrapper.find("[data-test=sheet-rate-60]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 60 }]);
  });

  it("chaque choix s’applique tout de suite", async () => {
    const wrapper = mountSheet();
    await wrapper.find("[data-test=sheet-view-to_review]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ view: "to_review" }]);
    await wrapper.find("[data-test=sheet-view-in_progress]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ view: "in_progress", sort: "activity" }]);
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
    expect(mountSheet({ minRate: 80 }).findAll("[data-test^=sheet-rate][aria-checked=true] .segmented-label").map((b) => b.text())).toEqual(["Dès 80 %"]);
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
    expect(wrapper.find(`#${group.attributes("aria-describedby")}`).text()).toBe("Provisoire : notée sur l’extrait de l’alerte");
    await group.find("[data-test=sheet-basis-provisional]").trigger("click");
    expect(wrapper.emitted("update")).toEqual([[{ basis: "provisional" }]]);
    const chosen = mountSheet({ basis: "provisional" });
    expect(chosen.findAll("[role=radiogroup][aria-labelledby=sheet-basis-title] [aria-checked=true]").map((b) => b.text())).toEqual(["Provisoires · 312"]);
    // Un seul arrêt de tabulation dans le groupe : le choix coché.
    expect(chosen.findAll("[data-test^=sheet-basis][tabindex='0']")).toHaveLength(1);
  });
});
