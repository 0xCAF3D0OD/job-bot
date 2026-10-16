import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import EngagementMoment from "./EngagementMoment.vue";

describe("EngagementMoment (docs/60 §2.1)", () => {
  it("félicite, rappelle l'ORP, et lance quelques confettis", () => {
    // En grand, par-dessus la page (hors de toute carte) ; « Fermer » ou Échap referment.
    const wrapper = mount(EngagementMoment, { props: { company: "Exemple SA" }, attachTo: document.body });
    const overlay = document.querySelector("[data-test=engagement-moment]")!;
    expect(overlay.textContent).toContain("Félicitations !");
    expect(overlay.textContent).toContain("Engagement chez Exemple SA. Pense à le signaler à ton conseiller ORP.");
    expect(overlay.querySelectorAll(".confetti span")).toHaveLength(24);
    expect(overlay.querySelector("[data-illustration=porte-ouverte]")).not.toBeNull();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });
});
