// Le mois ORP en une humeur (docs/123 §2, Q).
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FaceState from "./FaceState.vue";
import OrpMonth from "./OrpMonth.vue";

afterEach(() => vi.useRealTimers());

function at(day: number) {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 9, day, 9));
}

describe("OrpMonth", () => {
  it("un segment par candidature, « On rattrape » en orange", () => {
    at(16);
    const wrapper = mount(OrpMonth, { props: { title: "Mois ORP", count: 3, target: 10, month: "2026-10" } });
    expect(wrapper.findAll(".segment")).toHaveLength(10);
    expect(wrapper.findAll(".segment.done")).toHaveLength(3);
    expect(wrapper.find("[data-test=month-left]").text()).toBe("On rattrape. Il reste 7 candidatures en 11 jours ouvrables.");
    const tile = wrapper.find("[data-test=orp-face]");
    expect(tile.classes()).toEqual(expect.arrayContaining(["attentif", "act"]));
  });

  it("l'objectif atteint : ravi, sans orange", () => {
    at(24);
    const wrapper = mount(OrpMonth, { props: { title: "Mois ORP", count: 10, target: 10, month: "2026-10" } });
    expect(wrapper.find("[data-test=month-left]").text()).toBe("Objectif atteint. Le reste du mois est à toi.");
    expect(wrapper.find("[data-test=orp-face]").classes()).toContain("ravi");
    expect(wrapper.find("[data-test=orp-face]").classes()).not.toContain("act");
  });

  it("sans objectif : le compte seul, pas de visage", () => {
    const wrapper = mount(OrpMonth, { props: { title: "Mois ORP", count: 1, target: null, month: "2026-10" } });
    expect(wrapper.find("[data-test=month-count]").text().replace(/\s+/g, " ")).toBe("1 candidature");
    expect(wrapper.find("[data-test=orp-face]").exists()).toBe(false);
    expect(wrapper.find("[role=progressbar]").exists()).toBe(false);
  });
});

describe("FaceState (docs/123 §2, T)", () => {
  it("le visage décoratif, le titre, une ligne ; l'attente fait pulser", () => {
    const wrapper = mount(FaceState, { props: { title: "Aucune offre", waiting: true }, slots: { default: "<p>Rien.</p>" } });
    expect(wrapper.find("svg").attributes("aria-hidden")).toBe("true");
    expect(wrapper.find("svg").classes()).toContain("waiting");
    expect(wrapper.find("h2").text()).toBe("Aucune offre");
    expect(wrapper.find(".face-state-line").text()).toBe("Rien.");
  });
});
