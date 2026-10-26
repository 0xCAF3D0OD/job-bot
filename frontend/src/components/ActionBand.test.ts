import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ActionBand from "./ActionBand.vue";

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

describe("ActionBand (§3, la bande d'action)", () => {
  it("une région nommée par son titre, une phrase, un aperçu et une seule action, en lien", () => {
    const wrapper = mount(ActionBand, {
      props: { title: "Offres à examiner.", summary: "4 nouvelles depuis hier, dont 1 très proche.", action: "Commencer le tri", to: "/candidatures/tri" },
      slots: { default: "<p data-test='apercu'>La meilleure offre</p>" },
      global: { plugins: [router] },
    });
    const band = wrapper.find("[data-test=action-band]");
    const title = wrapper.find(".action-band-title");
    expect(band.element.tagName).toBe("SECTION");
    expect(band.attributes("aria-labelledby")).toBe(title.attributes("id"));
    expect(title.text()).toBe("Offres à examiner.");
    expect(wrapper.find(".action-band-summary").text()).toBe("4 nouvelles depuis hier, dont 1 très proche.");
    expect(wrapper.find("[data-test=apercu]").exists()).toBe(true);
    const actions = wrapper.findAll("[data-test=action-band-action]");
    expect(actions).toHaveLength(1);
    expect(actions[0]!.element.tagName).toBe("A");
    expect(actions[0]!.attributes("href")).toBe("/candidatures/tri");
    expect(actions[0]!.classes()).toContain("primary-link");
  });

  it("sans lien, l'action est un bouton principal qui prévient la page", async () => {
    const wrapper = mount(ActionBand, { props: { title: "Relances.", action: "Relancer" }, global: { plugins: [router] } });
    expect(wrapper.find(".action-band-summary").exists()).toBe(false);
    const button = wrapper.find("button[data-test=action-band-action]");
    expect(button.classes()).toContain("primary");
    await button.trigger("click");
    expect(wrapper.emitted("action")).toHaveLength(1);
  });
});
