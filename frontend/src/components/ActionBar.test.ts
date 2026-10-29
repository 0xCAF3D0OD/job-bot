import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ActionBar from "./ActionBar.vue";

describe("ActionBar", () => {
  it("rend son contenu et retire sa hauteur de la page en partant", () => {
    document.documentElement.style.setProperty("--action-bar-h", "120px");
    const wrapper = mount(ActionBar, { slots: { default: '<div class="action-bar-row"><button>Écarter</button><button>Garder</button></div>' } });
    expect(wrapper.find(".action-bar .action-bar-row").exists()).toBe(true);
    wrapper.unmount();
    expect(document.documentElement.style.getPropertyValue("--action-bar-h")).toBe("");
  });
});
