import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

function router() {
  const r = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:p(.*)*", component: { template: "<div />" } }] });
  void r.push("/reglages");
  return r;
}
const global = { plugins: [router()] };

describe("GroupedList et GroupedRow (règles §4)", () => {
  it("titre hors de la carte avec son compteur, une ligne par entrée", () => {
    const wrapper = mount(GroupedList, {
      props: { title: "À faire aujourd'hui", count: 9 },
      slots: { default: '<li class="grouped-item">a</li><li class="grouped-item">b</li>' },
      global,
    });
    expect(wrapper.find("h2").text()).toContain("À faire aujourd'hui");
    expect(wrapper.find(".count-badge").text()).toBe("9");
    expect(wrapper.find("section").attributes("aria-labelledby")).toBe(wrapper.find("h2").attributes("id"));
    expect(wrapper.findAll(".grouped-card > li")).toHaveLength(2);
  });

  it("un lien : un vrai <a href>, chevron, phrase reliée ; le clic simple passe par le routeur", async () => {
    const r = router();
    await r.isReady();
    const wrapper = mount(GroupedRow, { props: { title: "Notifications", description: "Seuil, message du jour", icon: "bell", to: "/reglages?rubrique=notifications" }, global: { plugins: [r] } });
    const link = wrapper.find("a.grouped-row");
    expect(link.attributes("href")).toBe("/reglages?rubrique=notifications");
    expect(link.find(".grouped-chevron").exists()).toBe(true);
    expect(link.attributes("aria-describedby")).toBe(wrapper.find(".grouped-row-description").attributes("id"));
    // Une ligne qui ne diffère que par la query n'est jamais marquée « page » d'elle-même.
    expect(link.attributes("aria-current")).toBeUndefined();
    await link.trigger("click", { button: 0 });
    await flushPromises();
    expect(r.currentRoute.value.fullPath).toBe("/reglages?rubrique=notifications");
  });

  it("une étiquette : la radio dans la ligne entière, sans chevron", () => {
    const wrapper = mount(GroupedRow, {
      props: { title: "Un message par jour", description: "Toutes les offres du jour, à 8 h.", label: true },
      slots: { start: '<input type="radio" name="rythme">' },
      global,
    });
    const label = wrapper.find("label.grouped-row");
    expect(label.find("input[type=radio]").exists()).toBe(true);
    expect(label.text()).toContain("Un message par jour");
    expect(wrapper.find(".grouped-chevron").exists()).toBe(false);
  });

  it("l'entrée affichée (liste et détail) : aria-current et la pastille de sélection", () => {
    const wrapper = mount(GroupedRow, { props: { title: "Notifications", to: "/reglages?rubrique=notifications", current: true }, global });
    const link = wrapper.find("a.grouped-row");
    expect(link.attributes("aria-current")).toBe("page");
    expect(link.classes()).toContain("grouped-row-current");
  });

  it("un bouton : émet click", async () => {
    const wrapper = mount(GroupedRow, { props: { title: "Taux minimum", value: "80 %", button: true }, global });
    await wrapper.find("button.grouped-row").trigger("click");
    expect(wrapper.emitted("click")).toHaveLength(1);
    expect(wrapper.find(".grouped-value").text()).toBe("80 %");
  });
});
