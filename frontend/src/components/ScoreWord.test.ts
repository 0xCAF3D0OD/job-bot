import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ScoreWord from "./ScoreWord.vue";

describe("La note d'une offre (règles §4, 1.6.5)", () => {
  it("le visage et un mot, sans jauge ; le visage cadré au plus près pour remplir ses 20 px", () => {
    const wrapper = mount(ScoreWord, { props: { score: 76 } });
    expect(wrapper.text()).toContain("Proche");
    expect(wrapper.find(".score-gauge").exists()).toBe(false);
    const face = wrapper.find("svg.face-mark");
    expect(face.attributes("width")).toBe("20");
    expect(face.attributes("viewBox")).toBe("13 15 74 74");
  });
});
