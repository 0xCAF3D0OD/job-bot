import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OfferCompatSheet from "./OfferCompatSheet.vue";

const base = {
  open: true,
  score: 76,
  verdict: "Proche de ton profil",
  tone: "close",
  subtitle: "Ingénieur DevOps · Exemple SA",
  how: ["La note compare l'annonce à ton profil."],
};

describe("OfferCompatSheet (§10.1, maquette OffreCompatibilite)", () => {
  it("deux familles avec leur nombre, libellé au-dessus de la valeur ; une famille vide n'est pas affichée", () => {
    const wrapper = mount(OfferCompatSheet, {
      attachTo: document.body,
      props: { ...base, strengths: [{ key: "Lieu", value: "Lausanne" }, { key: "", value: "Ton expérience correspond" }], gaps: [] },
    });
    expect(wrapper.find(".sheet-title").text()).toBe("Compatibilité");
    expect(wrapper.find(".compat-verdict").text()).toBe("Proche de ton profil");
    const strong = wrapper.find("[data-test=compat-ok]");
    expect(strong.find("h3").text()).toBe("Points forts · 2");
    expect(strong.attributes("aria-labelledby")).toBe(strong.find("h3").attributes("id"));
    const points = strong.findAll(".compat-point");
    expect(points[0]!.find(".compat-key").text()).toBe("Lieu");
    expect(points[0]!.find(".compat-value").text()).toBe("Lausanne");
    expect(points[1]!.find(".compat-key").exists()).toBe(false);
    expect(wrapper.find("[data-test=compat-gap]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("« Comment la note est calculée » se déplie sur place (pas de feuille depuis une feuille)", async () => {
    const wrapper = mount(OfferCompatSheet, {
      attachTo: document.body,
      props: { ...base, strengths: [], gaps: [{ key: "Langue", value: "allemand" }] },
    });
    expect(wrapper.find("[data-test=compat-gap] h3").text()).toBe("À vérifier · 1");
    const how = wrapper.find("[data-test=compat-how]");
    expect(how.attributes("aria-expanded")).toBe("false");
    await how.trigger("click");
    expect(how.attributes("aria-expanded")).toBe("true");
    expect(wrapper.find(`#${how.attributes("aria-controls")}`).text()).toContain("La note compare");
    expect(wrapper.findAll("dialog")).toHaveLength(1);
    wrapper.unmount();
  });
});
