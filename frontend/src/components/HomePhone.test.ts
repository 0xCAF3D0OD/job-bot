import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { Offer } from "../api/client";
import HomePhone from "./HomePhone.vue";
import LiquidCircle from "./LiquidCircle.vue";

const offer = (id: number, score: number): Offer =>
  ({ id, title: `Poste ${id}`, company: "Alpstack", location: "Lausanne", score, rate_min: 80, rate_max: 100, employment_type: "CDI", has_logo: false }) as unknown as Offer;

function home(props: Partial<InstanceType<typeof HomePhone>["$props"]> = {}) {
  return mount(HomePhone, {
    props: {
      name: "Kevin",
      firstDay: false,
      month: "2026-11",
      count: 2,
      target: 10,
      offers: [offer(1, 92), offer(2, 60)],
      emptyText: "Rien à trier · À demain",
      todos: [{ key: "follow", test: "todo-follow-ups", count: 13, label: "Relances à envoyer", to: "/candidatures/suivi" }],
      ...props,
    },
    global: { stubs: { RouterLink: RouterLinkStub } },
  });
}

describe("L'Accueil du téléphone (docs/139 étape 4)", () => {
  it("bonjour, ORP en cercle liquide, les offres et « Tout voir », À faire en nombres", () => {
    const view = home();
    expect(view.find("h1").text()).toBe("Bonjour Kevin.");
    expect(view.find("[data-test=home-tagline]").exists()).toBe(false);
    expect(view.find("[data-test=liquid-circle]").attributes("aria-label")).toBe("2 recherches sur 10");
    expect(view.find("[data-test=home-orp]").text()).toContain("Encore 8 d’ici le 5 décembre");
    expect(view.findAll("[data-test=home-card]")).toHaveLength(2);
    // L'anneau avec son chiffre, le mot dessous (2026-11-05, Kevin).
    const score = view.find("[data-test=home-card] [data-test=score]");
    expect(score.text()).toBe("92Très proche");
    expect(score.attributes("aria-label")).toBe("Très proche : 92 sur 100");
    // Ni bouton « Trier » ni bouton plein : « Tout voir » mène aux Candidatures (A3 annulé, maquette).
    expect(view.find("[data-test=home-triage]").exists()).toBe(false);
    expect(view.findAll(".primary-link")).toHaveLength(0);
    expect(view.find("[data-test=home-offers-all]").exists()).toBe(true);
    expect(view.find("[data-test=todo-follow-ups]").text()).toContain("13");
    expect(view.find("[data-test=todo-follow-ups]").text()).toContain("Relances à envoyer");
  });

  it("sans offre à trier : l'état vide du bloc", () => {
    const view = home({ offers: [] });
    expect(view.find("[data-test=home-offers-empty]").text()).toContain("Rien à trier");
    expect(view.find("[data-test=home-offers-all]").exists()).toBe(true);
  });

  it("l'accroche du premier jour, en français ; sans prénom, « Bonjour. »", () => {
    const view = home({ firstDay: true, name: null });
    expect(view.find("h1").text()).toBe("Bonjour.");
    expect(view.find("[data-test=home-tagline]").text()).toBe("Moins chercher,plus vivre.");
  });

  it("l'objectif atteint se dit", () => {
    expect(home({ count: 10 }).find("[data-test=home-orp]").text()).toContain("Objectif du mois atteint");
  });
});

describe("Le cercle liquide (D6)", () => {
  it("écrit toujours « x/y » et monte selon la part faite", () => {
    const circle = mount(LiquidCircle, { props: { count: 5, target: 10 } });
    expect(circle.find("text").text()).toBe("5/10");
    expect(circle.find("g[transform]").attributes("transform")).toBe("translate(0 50)");
  });
});
