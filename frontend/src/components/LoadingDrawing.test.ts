import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import LoadingDrawing from "./LoadingDrawing.vue";

describe("LoadingDrawing (docs/67, complément 0.55.1)", () => {
  it("insère le dessin animé unDraw, décoratif, aux couleurs du thème", async () => {
    const drawing = mount(LoadingDrawing, { props: { name: "morning-plans" } });
    await vi.waitFor(async () => {
      await flushPromises();
      expect(drawing.find("svg").exists()).toBe(true);
    });
    expect(drawing.classes()).toContain("drawing");
    expect(drawing.attributes("aria-hidden")).toBe("true");
    // Les animations sont propres au dessin (préfixe), jouées une fois.
    expect(drawing.html()).toContain("a-morning-plans-");
  });
});
