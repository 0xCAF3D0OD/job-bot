import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

const global = { stubs: { RouterLink: RouterLinkStub } };

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

  it("un lien : toute la ligne, chevron, phrase reliée", () => {
    const wrapper = mount(GroupedRow, { props: { title: "Notifications", description: "Seuil, message du jour", icon: "bell", to: "/reglages/notifications" }, global });
    const link = wrapper.findComponent(RouterLinkStub);
    expect(link.props("to")).toBe("/reglages/notifications");
    expect(link.find(".grouped-chevron").exists()).toBe(true);
    expect(link.attributes("aria-describedby")).toBe(wrapper.find(".grouped-row-description").attributes("id"));
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
    const link = wrapper.findComponent(RouterLinkStub);
    expect(link.attributes("aria-current")).toBe("page");
    expect(link.classes()).toContain("grouped-row-current");
    const other = mount(GroupedRow, { props: { title: "Rythme", to: "/reglages?rubrique=rythme" }, global });
    expect(other.findComponent(RouterLinkStub).attributes("aria-current")).toBeUndefined();
  });

  it("un bouton : émet click", async () => {
    const wrapper = mount(GroupedRow, { props: { title: "Taux minimum", value: "80 %", button: true }, global });
    await wrapper.find("button.grouped-row").trigger("click");
    expect(wrapper.emitted("click")).toHaveLength(1);
    expect(wrapper.find(".grouped-value").text()).toBe("80 %");
  });
});
