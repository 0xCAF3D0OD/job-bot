import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OfferBrief from "./OfferBrief.vue";

describe("OfferBrief, « Pour cette offre » (lot 15.1)", () => {
  it("points forts et à vérifier, le sujet avant les deux-points en gras, tout montré", () => {
    const offer = {
      summary_role: "Architecte cloud",
      score: 88,
      strengths: [{ text: "Kubernetes : plateforme de 40 services" }, { text: "Terraform" }],
      gaps: [{ text: "Allemand : niveau B2 demandé" }],
    };
    const wrapper = mount(OfferBrief, { props: { offer: offer as never } });
    expect(wrapper.find("[data-test=offer-brief-head]").text()).toBe("2 points forts · 1 à vérifier");
    // Plus de verdict ni de « Afficher moins ».
    expect(wrapper.find("[data-test=score]").exists()).toBe(false);
    expect(wrapper.find("[data-test=offer-brief-more]").exists()).toBe(false);
    const ok = wrapper.find("[data-test=offer-brief-ok]");
    expect(ok.find("h3").text()).toBe("Points forts (2)");
    expect(ok.findAll("strong").map((s) => s.text())).toEqual(["Kubernetes", "Terraform"]);
    expect(ok.find(".offer-brief-detail").text()).toBe("Plateforme de 40 services");
    const gap = wrapper.find("[data-test=offer-brief-gap]");
    expect(gap.find("h3").text()).toBe("À vérifier (1)");
    expect(gap.find("strong").text()).toBe("Allemand");
  });

  it("rien sans résumé de l'IA", () => {
    const wrapper = mount(OfferBrief, { props: { offer: { summary_role: null } as never } });
    expect(wrapper.find("[data-test=offer-brief]").exists()).toBe(false);
  });
});
