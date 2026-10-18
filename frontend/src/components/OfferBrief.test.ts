import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OfferBrief from "./OfferBrief.vue";

describe("OfferBrief, l'offre à côté de la lettre (docs/47 §2)", () => {
  it("note, nombre de points forts et de manques, repliés à 3 lignes", async () => {
    const offer = {
      summary_role: "Architecte cloud",
      score: 88,
      strengths: [{ text: "Kubernetes" }, { text: "Terraform" }, { text: "AWS" }],
      gaps: [{ text: "Allemand" }],
    };
    const wrapper = mount(OfferBrief, { props: { offer: offer as never } });
    expect(wrapper.find("[data-test=score]").attributes("aria-label")).toBe("Note de l'IA : 88 sur 100");
    expect(wrapper.text()).toContain("3 points forts · 1 manque");
    expect(wrapper.find("[data-test=offer-brief-points]").classes()).toContain("folded");
    await wrapper.find("[data-test=offer-brief-more]").trigger("click");
    expect(wrapper.find("[data-test=offer-brief-points]").classes()).not.toContain("folded");
  });

  it("rien sans résumé de l'IA", () => {
    const wrapper = mount(OfferBrief, { props: { offer: { summary_role: null } as never } });
    expect(wrapper.find("[data-test=offer-brief]").exists()).toBe(false);
  });
});
