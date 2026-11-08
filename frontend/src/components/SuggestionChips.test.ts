import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SuggestionChips from "./SuggestionChips.vue";

describe("SuggestionChips (docs/143)", () => {
  it("un clic propose le texte, sans rien envoyer", async () => {
    const wrapper = mount(SuggestionChips, { props: { items: ["Plus court", "Plus formel"], label: "Suggestions pour la lettre" } });
    expect(wrapper.get("ul").attributes("aria-label")).toBe("Suggestions pour la lettre");
    const buttons = wrapper.findAll("button");
    expect(buttons.map((b) => b.text())).toEqual(["Plus court", "Plus formel"]);
    await buttons[1]!.trigger("click");
    expect(wrapper.emitted("pick")).toEqual([["Plus formel"]]);
  });
});
