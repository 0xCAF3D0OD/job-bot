import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent } from "vue";

import DisclosureRow from "./DisclosureRow.vue";
import SidePanel from "./SidePanel.vue";

describe("Ligne dépliable (docs/32 §2.1)", () => {
  it("résumé à droite ; une seule ligne ouverte par groupe", async () => {
    const Pair = defineComponent({
      components: { DisclosureRow },
      template: `<div>
        <DisclosureRow title="Un" value="2 lignes" group="g"><p>contenu un</p></DisclosureRow>
        <DisclosureRow title="Deux" group="g"><p>contenu deux</p></DisclosureRow>
      </div>`,
    });
    const wrapper = mount(Pair);
    const [one, two] = wrapper.findAll(".disclosure");
    expect(one!.find(".disclosure-value").text()).toBe("2 lignes");
    expect(one!.find(".disclosure-panel").attributes("inert")).toBeDefined();
    await one!.find("button").trigger("click");
    expect(one!.classes()).toContain("open");
    expect(one!.find("button").attributes("aria-expanded")).toBe("true");
    await two!.find("button").trigger("click");
    expect(one!.classes()).not.toContain("open");
    expect(two!.classes()).toContain("open");
    await two!.find("button").trigger("click");
    expect(two!.classes()).not.toContain("open");
  });
});

describe("Panneau latéral (docs/32 §2.2)", () => {
  it("se ferme avec Échap, le × ou un clic à côté", async () => {
    const wrapper = mount(SidePanel, {
      props: { open: true, title: "Contacts chez Acme", help: "Aide" },
      slots: { default: "<p>dedans</p>" },
      global: { stubs: { teleport: true } },
      attachTo: document.body,
    });
    expect(wrapper.find("h2").text()).toBe("Contacts chez Acme");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await wrapper.find("[data-test=side-close]").trigger("click");
    await wrapper.find("[data-test=side-backdrop]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(3);
    wrapper.unmount();
  });
});
