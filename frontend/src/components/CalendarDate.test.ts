import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CalendarDate from "./CalendarDate.vue";

describe("CalendarDate (docs/143, D26)", () => {
  it("le mois en capitales, le jour, le ton et la taille ; décorative par défaut", () => {
    const wrapper = mount(CalendarDate, { props: { day: 30, month: 10, tone: "orp", size: 44 } });
    const svg = wrapper.get("svg");
    expect(svg.attributes("aria-hidden")).toBe("true");
    expect(svg.attributes("width")).toBe("44");
    expect(svg.attributes("height")).toBe("48");
    expect(svg.classes()).toContain("calendar-date-orp");
    expect(wrapper.text()).toContain("OCT");
    expect(wrapper.text()).toContain("30");
  });

  it("nommée quand `label` est donné", () => {
    const wrapper = mount(CalendarDate, { props: { day: 10, month: 11, label: "Mardi 10 novembre" } });
    expect(wrapper.get("svg").attributes("role")).toBe("img");
    expect(wrapper.get("svg").attributes("aria-label")).toBe("Mardi 10 novembre");
    expect(wrapper.get("svg").attributes("aria-hidden")).toBeUndefined();
  });
});
