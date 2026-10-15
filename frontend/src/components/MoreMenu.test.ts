import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import MoreMenu from "./MoreMenu.vue";

describe("MoreMenu (docs/50 §1)", () => {
  it("Échap ferme le seul menu et rend le focus ; les flèches passent d'une action à l'autre", async () => {
    const run = vi.fn();
    const outside = vi.fn();
    document.addEventListener("keydown", outside);
    const wrapper = mount(MoreMenu, {
      attachTo: document.body,
      props: {
        items: [
          { label: "Modifier", test: "edit", run },
          { label: "Supprimer", test: "remove", run: vi.fn(), danger: true },
        ],
      },
    });
    await wrapper.find("[data-test=more]").trigger("click");
    expect(document.activeElement?.getAttribute("data-test")).toBe("edit");
    await wrapper.find("[data-test=edit]").trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("remove");

    outside.mockClear();
    await wrapper.find("[data-test=remove]").trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    expect(document.activeElement?.getAttribute("data-test")).toBe("more");
    // Le panneau autour n'a rien reçu : il reste ouvert.
    expect(outside).not.toHaveBeenCalled();

    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=edit]").trigger("click");
    expect(run).toHaveBeenCalledOnce();
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    document.removeEventListener("keydown", outside);
    wrapper.unmount();
  });
});
