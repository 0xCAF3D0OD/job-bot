import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BottomSheet from "./BottomSheet.vue";

describe("BottomSheet (règles §4)", () => {
  it("titre à gauche, ✕ « Fermer », actions en bas ; ✕ et Échap ferment", async () => {
    const wrapper = mount(BottomSheet, {
      attachTo: document.body,
      props: { open: true, title: "Filtres" },
      slots: { default: "<p>Statut</p>", actions: '<button class="primary">Afficher 3 offres</button>' },
    });
    await wrapper.vm.$nextTick();
    const dialog = wrapper.find("dialog");
    expect(dialog.attributes("open")).toBeDefined();
    expect(dialog.attributes("aria-labelledby")).toBe(wrapper.find(".sheet-title").attributes("id"));
    expect(wrapper.find(".sheet-title").text()).toBe("Filtres");
    expect(wrapper.find(".sheet-actions").text()).toBe("Afficher 3 offres");
    await wrapper.find("[data-test=sheet-close]").trigger("click");
    await dialog.trigger("cancel");
    expect(wrapper.emitted("close")).toHaveLength(2);
    wrapper.unmount();
  });

  it("plein écran avec `full` (la cloche)", () => {
    const wrapper = mount(BottomSheet, { props: { open: false, title: "Alertes", full: true } });
    expect(wrapper.find("dialog").classes()).toContain("sheet-full");
  });
});
