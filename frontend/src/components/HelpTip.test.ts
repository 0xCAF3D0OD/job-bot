import { flushPromises, mount } from "@vue/test-utils";
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

  it("décale la bulle pour qu'elle reste dans l'écran", async () => {
    const rect = HTMLElement.prototype.getBoundingClientRect;
    HTMLElement.prototype.getBoundingClientRect = function () {
      return { left: -40, right: 216, top: 0, bottom: 40, width: 256, height: 40, x: -40, y: 0, toJSON: () => ({}) };
    };
    const wrapper = mount(HelpTip, { props: { text: "Aide." }, attachTo: document.body });
    await wrapper.find("[data-test=help-tip]").trigger("click");
    await flushPromises();
    expect((wrapper.find("[data-test=help-tip-text]").element as HTMLElement).style.marginLeft).toBe("48px");
    HTMLElement.prototype.getBoundingClientRect = rect;
    wrapper.unmount();
  });
});
