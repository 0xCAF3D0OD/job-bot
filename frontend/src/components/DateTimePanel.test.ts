import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import DateTimePanel from "./DateTimePanel.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

function panel(props: Record<string, unknown> = {}) {
  return mount(DateTimePanel, {
    attachTo: document.body,
    props: { date: "2026-11-10", time: "09:30", title: "Prochain rendez-vous", today: "2026-11-08", ...props },
  });
}

describe("DateTimePanel (docs/143, D26)", () => {
  it("6 semaines dès le lundi, jours passés désactivés, aujourd'hui et le jour choisi marqués", () => {
    const wrapper = panel();
    const days = wrapper.findAll(".dt-day");
    expect(days).toHaveLength(42);
    expect(days[0]!.attributes("data-day")).toBe("2026-10-26");
    expect(wrapper.get('[data-day="2026-11-07"]').attributes("disabled")).toBeDefined();
    expect(wrapper.get('[data-day="2026-11-08"]').attributes("aria-current")).toBe("date");
    expect(wrapper.get('[data-day="2026-11-10"]').attributes("aria-pressed")).toBe("true");
    expect(wrapper.get('[data-day="2026-11-10"]').attributes("aria-label")).toBe("10 novembre 2026");
    expect(wrapper.findAll(".dt-slot")).toHaveLength(17);
    expect(wrapper.get("[data-test=dt-summary]").text()).toBe("Mardi 10 novembre 2026, 9 h 30");
  });

  it("raccourcis, créneau et Valider", async () => {
    const wrapper = panel({ date: "", time: "" });
    expect(wrapper.get("[data-test=dt-confirm]").attributes("disabled")).toBeDefined();
    await wrapper.get('[data-test="dt-shortcut-Lundi prochain"]').trigger("click");
    await wrapper.get('[data-test="dt-slot-14:00"]').trigger("click");
    await wrapper.get("[data-test=dt-confirm]").trigger("click");
    expect(wrapper.emitted("confirm")).toEqual([[{ date: "2026-11-09", time: "14:00" }]]);
  });

  it("clavier : flèches pour les jours, Page bas pour les mois, Entrée valide, Échap annule", async () => {
    const wrapper = panel();
    await new Promise((resolve) => setTimeout(resolve));
    expect(document.activeElement?.getAttribute("data-day")).toBe("2026-11-10");
    const grid = wrapper.get(".dt-grid");
    await grid.trigger("keydown", { key: "ArrowRight" });
    await new Promise((resolve) => setTimeout(resolve));
    expect(document.activeElement?.getAttribute("data-day")).toBe("2026-11-11");
    await grid.trigger("keydown", { key: "PageDown" });
    await new Promise((resolve) => setTimeout(resolve));
    expect(document.activeElement?.getAttribute("data-day")).toBe("2026-12-11");
    (document.activeElement as HTMLElement).dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    expect(wrapper.emitted("confirm")).toEqual([[{ date: "2026-12-11", time: "09:30" }]]);
    await wrapper.get(".dt-panel").trigger("keydown", { key: "Escape" });
    expect(wrapper.emitted("cancel")).toHaveLength(1);
  });

  it("saisie libre : une date impossible est refusée sous le champ", async () => {
    const wrapper = panel();
    const input = wrapper.get("[data-test=dt-typed-date]");
    await input.setValue("31.02.2027");
    await input.trigger("change");
    expect(wrapper.get(".field-error").text()).toBe("Écris la date comme ceci : 10.11.2026.");
    await input.setValue("02.12.2026");
    await input.trigger("change");
    expect(wrapper.get('[data-day="2026-12-02"]').attributes("aria-pressed")).toBe("true");
  });
});
