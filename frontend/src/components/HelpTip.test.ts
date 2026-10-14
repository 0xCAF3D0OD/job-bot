import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import HelpTip from "./HelpTip.vue";

describe("HelpTip (docs/29 §2)", () => {
  it("s'ouvre au clic (toucher, clavier), se ferme avec Échap", async () => {
    const wrapper = mount(HelpTip, { props: { text: "Mon domaine : DevOps.", label: "Mots de Mon domaine" }, attachTo: document.body });
    const button = wrapper.find("[data-test=help-tip]");
    expect(button.attributes("aria-label")).toBe("Mots de Mon domaine");
    expect(wrapper.find("[data-test=help-tip-text]").exists()).toBe(false);
    await button.trigger("click");
    expect(button.attributes("aria-expanded")).toBe("true");
    expect(wrapper.find("[data-test=help-tip-text]").text()).toBe("Mon domaine : DevOps.");
    await wrapper.trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[data-test=help-tip-text]").exists()).toBe(false);
    wrapper.unmount();
  });
});
