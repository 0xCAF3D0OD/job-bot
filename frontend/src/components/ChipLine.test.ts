// La rangée d'étiquettes sur une ligne (lot du 11 novembre au soir, PR 46) : « Gardée », celles qui tiennent, « +k ».
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import ChipLine from "./ChipLine.vue";

const CHIPS = [
  { text: "Gardée", tone: "kept" as const },
  { text: "Provisoire", tone: "peach" as const },
  { text: "80–100 %" },
  { text: "CDD 12 mois" },
  { text: "Télétravail 2 j" },
  { text: "Ajoutée par toi", tone: "blue" as const },
];

// jsdom ne met rien en page : 70 px par étiquette, 30 pour la pastille, la rangée de la largeur donnée.
function layout(row: number): void {
  vi.spyOn(HTMLElement.prototype, "offsetWidth", "get").mockImplementation(function (this: HTMLElement) {
    return this.classList.contains("chip-more") ? 30 : 70;
  });
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(row);
}
afterEach(() => vi.restoreAllMocks());

describe("ChipLine (PR 46)", () => {
  it("6 étiquettes dans une carte de 390 px : « Gardée », celles qui tiennent, puis « +k », nommée « k autres étiquettes »", async () => {
    layout(310);
    const wrapper = mount(ChipLine, { props: { chips: CHIPS }, attachTo: document.body });
    await nextTick();
    const shown = wrapper.findAll("[data-test=offer-chip]").filter((c) => !c.classes("chip-off"));
    // 70 × 3 + 3 écarts de 0 (jsdom) + 30 = 240 ≤ 310 ; une quatrième étiquette ferait 310 avec la pastille : elle tient.
    expect(shown.map((c) => c.text())).toEqual(["Gardée", "Provisoire", "80–100 %", "CDD 12 mois"]);
    const more = wrapper.find("[data-test=chip-more]");
    expect(more.text()).toBe("+2");
    expect(more.attributes("aria-label")).toBe("2 autres étiquettes");
    // Les étiquettes retirées ne sont ni visibles ni lues.
    const off = wrapper.findAll("[data-test=offer-chip]").filter((c) => c.classes("chip-off"));
    expect(off.map((c) => c.attributes("aria-hidden"))).toEqual(["true", "true"]);
    wrapper.unmount();
  });

  it("« Gardée » n'est jamais retirée, même dans une rangée trop étroite", async () => {
    layout(60);
    const wrapper = mount(ChipLine, { props: { chips: CHIPS }, attachTo: document.body });
    await nextTick();
    const shown = wrapper.findAll("[data-test=offer-chip]").filter((c) => !c.classes("chip-off"));
    expect(shown.map((c) => c.text())).toEqual(["Gardée"]);
    expect(wrapper.find("[data-test=chip-more]").text()).toBe("+5");
    wrapper.unmount();
  });

  it("tout tient : pas de pastille", async () => {
    layout(600);
    const wrapper = mount(ChipLine, { props: { chips: CHIPS.slice(0, 3) }, attachTo: document.body });
    await nextTick();
    expect(wrapper.find("[data-test=chip-more]").exists()).toBe(false);
    wrapper.unmount();
  });
});
