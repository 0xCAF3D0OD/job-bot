import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DetailTwoColumns from "./DetailTwoColumns.vue";

describe("Gabarit deux colonnes (MODIFICATIONS du 8 novembre au soir, §2)", () => {
  const slots = {
    main: '<section class="detail-section"><h3>Statut</h3><button>Relancer</button></section>',
    aside: '<section class="detail-section"><h3>Documents</h3><a href="#">Lettre (Word)</a></section>',
  };

  it("la colonne principale, puis la colonne d'appui, dans l'ordre du DOM", () => {
    const wrapper = mount(DetailTwoColumns, { props: { asideLabel: "Documents et contacts" }, slots });
    const children = wrapper.find("[data-test=detail-columns]").element.children;
    expect(children).toHaveLength(2);
    expect(children[0]!.getAttribute("data-test")).toBe("detail-columns-main");
    expect(children[1]!.tagName).toBe("ASIDE");
    // La tabulation parcourt donc la principale avant l'appui.
    const focusable = [...wrapper.element.querySelectorAll("button, a")].map((el) => el.textContent);
    expect(focusable).toEqual(["Relancer", "Lettre (Word)"]);
  });

  it("la colonne d'appui porte son nom", () => {
    const wrapper = mount(DetailTwoColumns, { props: { asideLabel: "Documents et contacts" }, slots });
    expect(wrapper.find("aside").attributes("aria-label")).toBe("Documents et contacts");
  });

  it("la variante étroite des rendez-vous", () => {
    const wrapper = mount(DetailTwoColumns, { props: { asideLabel: "Le rendez-vous", narrow: true }, slots });
    expect(wrapper.classes()).toContain("detail-columns-narrow");
  });
});
