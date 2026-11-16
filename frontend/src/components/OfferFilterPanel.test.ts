import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, type OfferFilters } from "../composables/useOfferFilters";
import OfferFilterPanel from "./OfferFilterPanel.vue";

const facets = { sources: [], cantons: [], scores: [], unscored: 0, sure: 104, provisional: 312 };
const counts = { pending: 404, to_review: 38, filtered_out: 0, later: 9, in_progress: 45, expired: 0, all: 0 };

function mountPanel(patch: Partial<OfferFilters> = {}) {
  return mount(OfferFilterPanel, { props: { filters: { ...DEFAULT_FILTERS, ...patch }, counts, facets, total: 404 } });
}

const texts = (wrapper: ReturnType<typeof mountPanel>, prefix: string) => wrapper.findAll(`[data-test^=${prefix}]`).map((b) => b.text());

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
    ]);
    for (const id of ["pop-view", "pop-sort", "pop-score", "pop-basis", "pop-rate"]) expect(wrapper.find(`[aria-labelledby=${id}]`).exists()).toBe(true);
    expect(texts(wrapper, "pop-sort")).toEqual(["Par date", "Par note"]);
    expect(texts(wrapper, "pop-score")).toEqual(["Toutes", "50 et +", "75 et +", "85 et +"]);
    expect(texts(wrapper, "pop-basis")).toEqual(["Toutes", "Définitives · 104", "Provisoires · 312"]);
    expect(texts(wrapper, "pop-rate")).toEqual(["Tous", "Dès 60 %", "Dès 80 %", "100 %"]);
    expect(wrapper.find("[data-test=pop-remote]").element.closest("label")?.textContent).toBe("Télétravail possible, même partiel");
    // Section 35 du 16.11 : l'interrupteur des agences, sous Télétravail.
    expect(wrapper.text()).toContain("Masquer les agences de placement");
  });

  it("les textes d’aide, reliés par aria-describedby", () => {
    const wrapper = mountPanel();
    for (const button of wrapper.findAll("[data-test^=pop-score]"))
      expect(wrapper.find(`#${button.attributes("aria-describedby")}`).text()).toBe("À quel point l’offre correspond à ton profil.");
    const basis = wrapper.find("[role=radiogroup][aria-labelledby=pop-basis]");
    expect(wrapper.find(`#${basis.attributes("aria-describedby")}`).text()).toBe("Provisoire : notée sur l’extrait de l’alerte, sans l’annonce complète.");
  });

  it("mêmes seuils (50, 75, 85) et mêmes taux, un seul choix marqué", async () => {
    for (const min of [50, 75, 85])
      expect(mountPanel({ minScore: min }).findAll("[data-test^=pop-score][aria-pressed=true]").map((b) => b.attributes("data-test"))).toEqual([`pop-score-${min}`]);
    expect(mountPanel({ minRate: 80 }).findAll("[data-test^=pop-rate][aria-pressed=true]").map((b) => b.text())).toEqual(["Dès 80 %"]);
    // Une adresse d'avant (?note=60-90) : aucun choix marqué.
    expect(mountPanel({ minScore: 60, maxScore: 90 }).findAll("[data-test^=pop-score][aria-pressed=true]")).toHaveLength(0);
    const wrapper = mountPanel();
    await wrapper.find("[data-test=pop-score-75]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minScore: 75, maxScore: null }]);
    await wrapper.find("[data-test=pop-rate-60]").trigger("click");
    expect(wrapper.emitted("update")?.at(-1)).toEqual([{ minRate: 60 }]);
  });
});
