import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ScoreWord from "./ScoreWord.vue";

describe("La note d'une offre (règles §4, 1.6.6)", () => {
  it("le visage, un mot et une jauge discrète ; le visage cadré au plus près pour remplir ses 20 px", () => {
    const wrapper = mount(ScoreWord, { props: { score: 76 } });
    expect(wrapper.text()).toContain("Proche");
    expect(wrapper.find(".score-gauge").attributes("style")).toContain("--p: 76");
    const face = wrapper.find("svg.face-mark");
    expect(face.attributes("width")).toBe("20");
    expect(face.attributes("viewBox")).toBe("13 15 74 74");
  });
});
