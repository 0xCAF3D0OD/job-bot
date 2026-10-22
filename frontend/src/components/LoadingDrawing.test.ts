import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import LoadingDrawing from "./LoadingDrawing.vue";

describe("LoadingDrawing (docs/67, complément 0.55.1)", () => {
  it("insère le dessin animé unDraw, décoratif, aux couleurs du thème", async () => {
    // Chargé d'abord, attente large : sous charge, sa première préparation peut être lente
    // (docs/69 §5).
    await import("../assets/dessins/maintenance.svg?raw");
    const drawing = mount(LoadingDrawing, { props: { name: "maintenance" } });
    await vi.waitFor(
      async () => {
        await flushPromises();
        expect(drawing.find("svg").exists()).toBe(true);
      },
      { timeout: 5000 },
    );
    expect(drawing.classes()).toContain("drawing");
    expect(drawing.attributes("aria-hidden")).toBe("true");
    // Les animations sont propres au dessin (préfixe).
    expect(drawing.html()).toContain("a-maintenance-");
  });
});
