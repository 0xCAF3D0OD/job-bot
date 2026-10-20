import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";

import HoverNote from "./HoverNote.vue";

vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone: ref(true) }) }));

describe("HoverNote au doigt (docs/108 §2)", () => {
  it("le « i » ouvre la description sous le titre ; une seule à la fois ; pas dans un bouton", async () => {
    const Page = defineComponent(() => () =>
      h("div", [
        h("label", h(HoverNote, { text: "Communes ou cantons." }, () => "Lieux")),
        h("legend", h(HoverNote, { text: "Les autres jours, rien n'arrive." }, () => "Jours de recherche")),
        h("button", h(HoverNote, { text: "Environ 0,05 $." }, () => "Préparer le CV")),
      ]),
    );
    const wrapper = mount(Page, { attachTo: document.body });
    await wrapper.vm.$nextTick();
    const infos = wrapper.findAll("[data-test=hover-note-info]");
    expect(infos).toHaveLength(2);
    await infos[0]!.trigger("click");
    expect(wrapper.find("[data-test=hover-note-line]").text()).toBe("Communes ou cantons.");
    expect(infos[0]!.attributes("aria-expanded")).toBe("true");
    await infos[1]!.trigger("click");
    const lines = wrapper.findAll("[data-test=hover-note-line]");
    expect(lines).toHaveLength(1);
    expect(lines[0]!.text()).toBe("Les autres jours, rien n'arrive.");
    await infos[1]!.trigger("click");
    expect(wrapper.find("[data-test=hover-note-line]").exists()).toBe(false);
    wrapper.unmount();
  });
});
