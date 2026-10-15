import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import Illustration from "./Illustration.vue";

describe("Illustration (docs/58)", () => {
  it("insère le dessin, décoratif par défaut, décrit quand on lui donne un texte", async () => {
    const plain = mount(Illustration, { props: { name: "date-picker" } });
    await vi.waitFor(async () => {
      await flushPromises();
      expect(plain.find("svg").exists()).toBe(true);
    });
    expect(plain.attributes("aria-hidden")).toBe("true");
    // Les animations sont propres à l'illustration (préfixe), sans forme ajoutée.
    expect(plain.html()).toContain("a-date-picker-");
    const told = mount(Illustration, { props: { name: "date-picker", label: "Fait" } });
    expect(told.attributes("role")).toBe("img");
    expect(told.attributes("aria-label")).toBe("Fait");
  });
});
