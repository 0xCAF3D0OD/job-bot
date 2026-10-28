import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BusyButton from "./BusyButton.vue";

describe("BusyButton (planche « vide et chargement »)", () => {
  it("pendant l'action : aria-disabled sans disabled, clic ignoré, état annoncé", async () => {
    const wrapper = mount(BusyButton, {
      props: { busy: false, busyLabel: "Rédaction…" },
      slots: { default: "Rédiger la relance" },
      attrs: { class: "primary" },
    });
    const button = wrapper.find("button");
    expect(button.classes()).toContain("primary");
    expect(button.attributes("aria-disabled")).toBeUndefined();
    await button.trigger("click");
    expect(wrapper.emitted("click")).toHaveLength(1);

    await wrapper.setProps({ busy: true });
    expect(button.attributes("aria-disabled")).toBe("true");
    expect(button.attributes("disabled")).toBeUndefined();
    await button.trigger("click");
    expect(wrapper.emitted("click")).toHaveLength(1);
    expect(wrapper.find("[role=status]").text()).toBe("Rédaction…");
    // Les deux libellés restent dans le bouton : sa largeur ne change pas.
    expect(button.findAll(".busy-label")).toHaveLength(2);
  });
});
