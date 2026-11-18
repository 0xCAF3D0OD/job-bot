import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, type OfferFilters } from "../composables/useOfferFilters";
import OfferFilterPanel from "./OfferFilterPanel.vue";

const facets = { sources: [], cantons: [], scores: [], unscored: 0, sure: 104, provisional: 312, rates: [], contracts: [], distances: [] };
const counts = { pending: 404, to_review: 38, filtered_out: 0, later: 9, in_progress: 45, expired: 0, all: 0 };

function mountPanel(patch: Partial<OfferFilters> = {}) {
  return mount(OfferFilterPanel, { props: { filters: { ...DEFAULT_FILTERS, ...patch }, counts, facets, total: 404 } });
}

const texts = (wrapper: ReturnType<typeof mountPanel>, prefix: string) =>
  wrapper.findAll(`[data-test^=${prefix}]`).map((b) => (b.find(".filter-panel-label").exists() ? b.find(".filter-panel-label") : b).text());

// Section 31 du 16.11 : « Filtres : des mots que tout le monde comprend » (panneau de CandidaturesOrdinateurB).
describe("Le panneau Filtres de l’ordinateur (section 31)", () => {
  it("titres et choix compréhensibles, chaque titre relié à son groupe", () => {
    const wrapper = mountPanel();
    expect(wrapper.findAll(".filter-panel-group > span").map((s) => s.text())).toEqual([
      "Statut",
      "Trier",
      "Note minimale, sur 100",
      "Type de note",
      "Taux d’activité",
      "Contrat",
    ]);
    for (const id of ["pop-view", "pop-sort", "pop-score", "pop-basis", "pop-rate", "pop-contract"]) expect(wrapper.find(`[aria-labelledby=${id}]`).exists()).toBe(true);
    expect(texts(wrapper, "pop-sort")).toEqual(["Par date", "Par note"]);
    expect(texts(wrapper, "pop-score")).toEqual(["Toutes", "50 et +", "75 et +", "85 et +"]);
    expect(texts(wrapper, "pop-basis")).toEqual(["Toutes", "Définitives · 104", "Provisoires · 312"]);
    expect(texts(wrapper, "pop-rate")).toEqual(["Tous", "Dès 60 %", "Dès 80 %", "100 %"]);
    expect(wrapper.find("[data-test=pop-remote]").element.closest("label")?.textContent).toBe("Télétravail possible, même partiel");
    // Section 35 du 16.11 : l'interrupteur des agences, sous Télétravail.
    expect(wrapper.text()).toContain("Masquer les agences de placement");
  });

  it("pas de phrase d’aide sous la note ni sous le type de note (§72g du 18.11)", () => {
    const wrapper = mountPanel();
    expect(wrapper.find("[aria-describedby]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("correspond à ton profil");
    expect(wrapper.text()).not.toContain("extrait de l’alerte");
  });

  it("mêmes seuils (50, 75, 85) et mêmes taux, un seul choix marqué", async () => {
    for (const min of [50, 75, 85])
      expect(mountPanel({ minScore: min }).findAll("[data-test^=pop-score][aria-pressed=true]").map((b) => b.attributes("data-test"))).toEqual([`pop-score-${min}`]);
    expect(mountPanel({ minRate: 80 }).findAll("[data-test^=pop-rate][aria-pressed=true]").map((b) => b.attributes("data-test"))).toEqual(["pop-rate-80"]);
    // Une adresse d'avant (?note=60-90) : aucun choix marqué.
    expect(mountPanel({ minScore: 60, maxScore: 90 }).findAll("[data-test^=pop-score][aria-pressed=true]")).toHaveLength(0);
    const wrapper = mountPanel();
    await wrapper.find("[data-test=pop-score-75]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: 75, maxScore: null }]);
    await wrapper.find("[data-test=pop-rate-60]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 60 }]);
  });

  // Kevin, 18.11 : les nombres de la feuille du téléphone aussi sur l'ordinateur, même calcul ; un choix à 0 grisé.
  it("le nombre d'offres sous chaque choix de Note et de Taux, le choix actif égal à « Afficher n offres »", () => {
    const scores = [...Array(10).fill(1), ...Array(5).fill(10), 6, 7, 0, 0, 0];
    const rates = [{ value: "all", count: 84 }, { value: "60", count: 72 }, { value: "80", count: 0 }, { value: "100", count: 120000 }];
    const wrapper = mount(OfferFilterPanel, {
      props: { filters: { ...DEFAULT_FILTERS, minScore: 75 }, counts, facets: { ...facets, scores, unscored: 3, rates }, total: 13 },
    });
    const subs = (prefix: string) => wrapper.findAll(`[data-test^=${prefix}] .filter-panel-sub`).map((s) => s.text());
    expect(subs("pop-score")).toEqual(["76", "63", "13", "0"]);
    expect(subs("pop-rate")).toEqual(["84", "72", "0", "100 k+"]);
    expect(wrapper.find("[data-test=pop-score-75] .filter-panel-sub").text()).toBe("13");
    expect(wrapper.find("[data-test=filters-done]").text()).toBe("Afficher 13 offres");
    // À 0 : grisé, toujours cliquable ; le choix actif n'est jamais grisé.
    expect(wrapper.find("[data-test=pop-score-85]").classes()).toContain("choice-empty");
    expect(wrapper.find("[data-test=pop-rate-80]").classes()).toContain("choice-empty");
    expect(wrapper.find("[data-test=pop-rate-80]").attributes("disabled")).toBeUndefined();
    expect(wrapper.find("[data-test=pop-score-75]").classes()).not.toContain("choice-empty");
  });

  it("Contrat : « CDI · 120 », plusieurs choix, un choix à 0 grisé mais cliquable (issue 468)", async () => {
    const contracts = [{ value: "cdi", count: 120 }, { value: "non_precise", count: 7 }];
    const wrapper = mount(OfferFilterPanel, {
      props: { filters: { ...DEFAULT_FILTERS, contracts: ["non_precise"] }, counts, facets: { ...facets, contracts }, total: 7 },
    });
    expect(texts(wrapper, "pop-contract")).toEqual(["CDI · 120", "CDD · 0", "Stage · 0", "Temporaire · 0", "Non précisé · 7"]);
    expect(wrapper.find("[data-test=pop-contract-non_precise]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=pop-contract-cdd]").classes()).toContain("choice-empty");
    await wrapper.find("[data-test=pop-contract-cdd]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ contracts: ["cdd", "non_precise"] }]);
  });
});
