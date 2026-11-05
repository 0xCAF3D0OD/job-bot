// L'anneau de la note (maquette Systeme, règle 1 ; D3, D5).
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ScoreRing from "./ScoreRing.vue";

const arc = (wrapper: ReturnType<typeof mount>) => wrapper.find(".score-ring-arc").attributes("stroke-dasharray");

describe("ScoreRing", () => {
  it("piste complète, graduations tous les 25 %, arc proportionnel à la note, couleur du mot", () => {
    const wrapper = mount(ScoreRing, { props: { score: 75, worded: true } });
    const ring = wrapper.find("[data-test=score]");
    expect(wrapper.find(".score-ring-track").exists()).toBe(true);
    expect(wrapper.find(".score-ring-ticks").attributes("d")).toBe("M50 1V15M85 50H99M50 85V99M1 50H15");
    expect(arc(wrapper)).toBe("197.92 263.89");
    // Proche (dès 75) : vert, jamais le bleu par défaut ; le chiffre au centre, le mot dessous (2026-11-05, Kevin).
    expect(wrapper.find(".score-ring").classes()).toContain("close");
    expect(wrapper.find(".score-ring-value").text()).toBe("75");
    expect(wrapper.find(".score-ring-word").text()).toBe("Proche");
    expect(mount(ScoreRing, { props: { score: 74, worded: true } }).find(".score-ring-word").text()).toBe("À creuser");
    expect(ring.attributes("aria-label")).toBe("Proche : 75 sur 100");
  });

  it("garde l'arc entre vide et plein, et signale une note ancienne", () => {
    const full = mount(ScoreRing, { props: { score: 130, stale: true } });
    expect(arc(full)).toBe("263.89 263.89");
    expect(full.find("[data-test=score]").attributes("aria-label")).toContain("ancien profil");
    expect(arc(mount(ScoreRing, { props: { score: -5 } }))).toBe("0.00 263.89");
  });

  it("sans note : pas d'anneau, « Pas encore notée » en texte, la raison pour les lecteurs d'écran", () => {
    const wrapper = mount(ScoreRing, { props: { score: null, pending: "Pas encore notée, à noter", worded: true } });
    expect(wrapper.find("svg").exists()).toBe(false);
    expect(wrapper.find("[data-test=score]").classes()).toContain("score-pending");
    expect(wrapper.find("[data-test=score]").attributes("title")).toBe("Pas encore notée, à noter");
    expect(wrapper.find("[data-test=score]").text()).toContain("Pas encore notée");
  });

  it("le grand cercle de la fiche (bare) : le chiffre seul, sans « /100 » qui déborde", () => {
    expect(mount(ScoreRing, { props: { score: 87, large: true, bare: true } }).find(".score-ring").text()).toBe("87");
  });

  it("montre « /100 » dans le grand cercle du panneau", () => {
    expect(mount(ScoreRing, { props: { score: 42, large: true } }).text()).toBe("42/100");
  });
});
