/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

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

  it("sous 600 px, le pied de page réserve la place du panneau : ses liens ne passent pas dessous", () => {
    const css = readFileSync(resolve(__dirname, "../style.css"), "utf8");
    expect(css).toMatch(/:root:has\(\.action-bar\) \.app-footer \{ padding-bottom: calc\([^}]*var\(--action-bar-h/);
    expect(css).toContain(":root:has(.action-bar):has(.app-footer) main { padding-bottom: var(--space-6); }");
  });
});
