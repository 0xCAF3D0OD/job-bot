import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ShowMore from "./ShowMore.vue";

describe("ShowMore (règles §4)", () => {
  it("« Afficher plus (4) » puis « Afficher moins », avec aria-expanded", async () => {
    const wrapper = mount(ShowMore, {
      props: { hidden: 4, modelValue: false, "onUpdate:modelValue": (v: boolean) => wrapper.setProps({ modelValue: v }) },
    });
    const button = wrapper.find("button");
    expect(button.text()).toBe("Afficher plus (4)");
    expect(button.attributes("aria-expanded")).toBe("false");
    await button.trigger("click");
    expect(button.text()).toBe("Afficher moins");
    expect(button.attributes("aria-expanded")).toBe("true");
  });
});
