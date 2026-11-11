import { mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import type { Offer } from "../api/client";
import HomePhone from "./HomePhone.vue";

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

describe("L’Accueil du téléphone (docs/139 étape 4)", () => {
  it("bonjour, la barre ORP, les offres et « Tout voir », À faire en nombres", () => {
    const view = home();
    expect(view.find("h1").text()).toBe("Bonjour Kevin.");
    expect(view.find("[data-test=home-tagline]").exists()).toBe(false);
    // La barre ORP (PR 48) : le mois, le compte, ce qui reste et le rythme ; « Voir le suivi » mène au Bilan.
    const bar = view.find("[data-test=orp-bar]");
    expect(bar.text()).toContain("Mois ORP · novembre");
    expect(bar.find("[data-test=month-count]").text()).toBe("2 sur 10");
    expect(bar.find("[role=progressbar]").attributes("aria-valuenow")).toBe("2");
    expect(bar.find("[data-test=month-left]").text()).toMatch(/^Encore 8 d’ici le 5 décembre · (dans les temps|en retard)$/);
    expect(view.find("[data-test=home-orp]").text()).toBe("Voir le suivi");
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

  it("sans offre à trier : l’état vide du bloc", () => {
    const view = home({ offers: [] });
    expect(view.find("[data-test=home-offers-empty]").text()).toContain("Rien à trier");
    expect(view.find("[data-test=home-offers-all]").exists()).toBe(true);
  });

  it("l’accroche du premier jour, en français ; sans prénom, « Bonjour. »", () => {
    const view = home({ firstDay: true, name: null });
    expect(view.find("h1").text()).toBe("Bonjour.");
    expect(view.find("[data-test=home-tagline]").text()).toBe("Moins chercher,plus vivre.");
  });

  it("l’objectif atteint se dit", () => {
    expect(home({ count: 10 }).find("[data-test=month-left]").text()).toBe("Objectif atteint");
  });
});

describe("L’Accueil du téléphone : les bandes", () => {
  describe("les bandes qui s’empilent (PR 36)", () => {
    afterEach(() => vi.unstubAllGlobals());
    const motion = (reduce: boolean) =>
      vi.stubGlobal("matchMedia", (query: string) => ({ matches: reduce && query.includes("reduce"), addEventListener() {}, removeEventListener() {} }));

    it("ORP et Offres collent quand elles tiennent dans l’écran ; « À faire » ne colle jamais", async () => {
      motion(false);
      const view = home();
      await nextTick();
      expect(view.get("[data-test=home-band-orp]").classes()).toContain("home-stick");
      expect(view.get("[data-test=home-band-offers]").classes()).toContain("home-stick");
      expect(view.get("[data-test=home-todo]").classes()).not.toContain("home-stick");
    });

    it("animations réduites : rien ne colle", async () => {
      motion(true);
      const view = home();
      await nextTick();
      expect(view.find(".home-stick").exists()).toBe(false);
    });

    it("une bande plus haute que l’écran ne colle pas", async () => {
      motion(false);
      vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(5000);
      const view = home();
      await nextTick();
      expect(view.find(".home-stick").exists()).toBe(false);
      vi.restoreAllMocks();
    });
  });
});
