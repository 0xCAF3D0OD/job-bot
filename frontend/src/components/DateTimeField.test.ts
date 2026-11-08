import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DateTimeField from "./DateTimeField.vue";

describe("DateTimeField (docs/143, D26)", () => {
  it("la date et l'heure en toutes lettres, nommées, et le choix ouvert", async () => {
    const wrapper = mount(DateTimeField, { props: { date: "2026-11-10", time: "09:30", open: "date" } });
    const date = wrapper.get("[data-test=dt-date]");
    expect(date.text()).toContain("Mardi 10 novembre 2026");
    expect(date.attributes("aria-label")).toBe("Date : Mardi 10 novembre 2026");
    expect(date.attributes("aria-expanded")).toBe("true");
    expect(wrapper.get("[data-test=dt-time]").text()).toContain("9 h 30");
    await wrapper.get("[data-test=dt-time]").trigger("click");
    expect(wrapper.emitted("open")).toEqual([["time"]]);
  });

  it("abrégée sur le téléphone, et une invite sans valeur", () => {
    const wrapper = mount(DateTimeField, { props: { date: "2026-11-10", time: "", compact: true } });
    expect(wrapper.get("[data-test=dt-date]").text()).toContain("Mar. 10 nov. 2026");
    expect(wrapper.get("[data-test=dt-time]").text()).toContain("Choisir une heure");
  });
});
