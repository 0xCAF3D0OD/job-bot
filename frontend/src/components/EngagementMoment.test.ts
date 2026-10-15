import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import EngagementMoment from "./EngagementMoment.vue";

describe("EngagementMoment (docs/60 §2.1)", () => {
  it("félicite, rappelle l'ORP, et lance quelques confettis", () => {
    const wrapper = mount(EngagementMoment, { props: { company: "Exemple SA" } });
    expect(wrapper.text()).toContain("Félicitations !");
    expect(wrapper.text()).toContain("Engagement chez Exemple SA. Pense à le signaler à ton conseiller ORP.");
    expect(wrapper.findAll(".confetti span")).toHaveLength(18);
    expect(wrapper.find("[data-illustration=handshake-deal]").exists()).toBe(true);
  });
});
