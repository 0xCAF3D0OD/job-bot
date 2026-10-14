import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { fromQuery, toQuery, DEFAULT_FILTERS } from "../composables/useOfferFilters";
import ScoreCurve from "./ScoreCurve.vue";

const BINS = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 5, 8, 6, 4, 2, 1, 0, 0, 0];

describe("ScoreCurve (docs/27 §3)", () => {
  it("la partie verte est la même courbe que le fond gris, découpée entre les poignées", () => {
    const wrapper = mount(ScoreCurve, { props: { bins: BINS, min: 60, max: 90, unscored: 4 } });
    const [all, chosen] = wrapper.findAll("path");
    expect(chosen!.attributes("d")).toBe(all!.attributes("d"));
    const rect = wrapper.find("clipPath rect");
    expect(Number(rect.attributes("x"))).toBeCloseTo(180);
    expect(Number(rect.attributes("width"))).toBeCloseTo(90);
    expect(wrapper.text()).toContain("4 offres pas encore notées : masquées");
  });

  it("rend les bornes choisies, sans borne inutile", async () => {
    const wrapper = mount(ScoreCurve, { props: { bins: BINS, min: null, max: null, unscored: 0 } });
    await wrapper.find("[data-test=score-min-field]").setValue("65");
    await wrapper.find("[data-test=score-min-field]").trigger("change");
    expect(wrapper.emitted("change")?.at(-1)).toEqual([65, null]);
    await wrapper.find("[data-test=score-max-field]").setValue("40");
    await wrapper.find("[data-test=score-max-field]").trigger("change");
    expect(wrapper.emitted("change")?.at(-1)).toEqual([40, 65]); // bornes remises dans l'ordre
  });

  it("sans offre notée, un message à la place de la courbe", () => {
    const wrapper = mount(ScoreCurve, { props: { bins: Array(20).fill(0), min: null, max: null, unscored: 3 } });
    expect(wrapper.find("svg").exists()).toBe(false);
    expect(wrapper.text()).toContain("Aucune offre notée");
  });

  it("garde la plage de notes dans l'adresse", () => {
    expect(toQuery({ ...DEFAULT_FILTERS, minScore: 60, maxScore: 90 })).toEqual({ note: "60-90" });
    expect(toQuery({ ...DEFAULT_FILTERS, minScore: 60 })).toEqual({ note: "60" });
    expect(toQuery({ ...DEFAULT_FILTERS, maxScore: 50 })).toEqual({ note: "0-50" });
    const read = fromQuery({ note: "60-90" });
    expect([read.minScore, read.maxScore]).toEqual([60, 90]);
    expect(fromQuery({ note: "70" }).maxScore).toBeNull();
  });
});
