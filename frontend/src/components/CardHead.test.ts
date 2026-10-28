import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CardHead from "./CardHead.vue";

const global = { stubs: { RouterLink: RouterLinkStub } };

describe("CardHead (règles §4)", () => {
  it("« Titre · nombre » à gauche, « Tout voir » vers la page à droite", () => {
    const wrapper = mount(CardHead, { props: { title: "À relancer", count: 3, to: "/suivi" }, global });
    expect(wrapper.find("h2").text()).toBe("À relancer · 3");
    expect(wrapper.findComponent(RouterLinkStub).props("to")).toBe("/suivi");
    expect(wrapper.find("[data-test=card-all]").text()).toBe("Tout voir");
  });

  it("sans lien ni action, pas de zone d'actions ; une action passe par le slot", () => {
    expect(mount(CardHead, { props: { title: "Contacts" }, global }).find(".card-head-actions").exists()).toBe(false);
    const withAction = mount(CardHead, {
      props: { title: "Contacts", count: 0, level: 3 },
      slots: { default: "<button>+ Ajouter</button>" },
      global,
    });
    expect(withAction.find("h3").text()).toBe("Contacts · 0");
    expect(withAction.find(".card-head-actions button").text()).toBe("+ Ajouter");
  });
});
