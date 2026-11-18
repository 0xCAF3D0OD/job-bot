import { mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import type { Offer } from "../api/client";
import HomePhone from "./HomePhone.vue";
import LiquidCircle from "./LiquidCircle.vue";

const offer = (id: number, score: number, asks: { text: string; covered: boolean }[] = []): Offer =>
  ({ id, title: `Poste ${id}`, company: "Alpstack", location: "Lausanne", score, rate_min: 80, rate_max: 100, employment_type: "CDI", has_logo: false, keywords_asks: asks }) as unknown as Offer;

const late = { lines: [{ text: "1 justificatif en retard,", tone: "late" as const }, { text: "puis 2 candidatures", tone: "blue" as const }], lead: "", hand: "", sub: "Commence par l’ORP : 2 minutes." };
const task = (key: string, verb: string, rest: string, detail: string, extra = {}) => ({ key, test: key, verb, rest, detail, to: "/", tone: "normal" as const, ...extra });

function home(props: Partial<InstanceType<typeof HomePhone>["$props"]> = {}) {
  return mount(HomePhone, {
    props: {
      name: "Kevin",
      firstDay: false,
      month: "2026-11",
      count: 7,
      target: 10,
      pace: true,
      week: { count: 2, target: 3 },
      title: late,
      tasks: [
        task("orp-urgent", "Remettre", "les justificatifs d’octobre", "En retard depuis le 5 novembre", { check: true, tone: "late" }),
        task("preparing", "Préparer", "2 candidatures", "2 offres gardées attendent leur lettre"),
        task("triage", "Trier", "1 offre", "Pas encore vues"),
      ],
      rest: false,
      top: [offer(1, 92)],
      toSort: [offer(2, 60, [{ text: "Azure", covered: false }, { text: "Ansible", covered: true }])],
      orpDone: null,
      orpBusy: false,
      ...props,
    },
    global: { stubs: { RouterLink: RouterLinkStub } },
  });
}

describe("L’Accueil du téléphone (AccueilV2, §40 du 17.11)", () => {
  it("le titre à la main, puis À faire, ORP, Top du jour et les offres à trier, dans cet ordre", () => {
    const view = home();
    const title = view.get("[data-test=home-title]");
    expect(title.text()).toBe("1 justificatif en retard,puis 2 candidatures");
    expect(title.find(".home-hand-late").exists()).toBe(true);
    expect(view.get("[data-test=home-sub]").text()).toBe("Commence par l’ORP : 2 minutes.");
    const order = view.findAll("section").map((s) => s.attributes("data-test"));
    expect(order).toEqual(["home-todo", "home-band-orp", "home-top", "home-band-offers"]);
  });

  it("À faire : numéros, verbe en gras et ligne de détail ; le cercle orange pour les justificatifs (§61)", async () => {
    // Sans mise en page (jsdom), toutes les feuilles se croiraient recouvertes : on les garde dans le flux.
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(5000);
    const view = home();
    expect(view.get("[data-test=todo-preparing]").text()).toContain("Préparer 2 candidatures");
    expect(view.get("[data-test=todo-preparing] .home-num").text()).toBe("2");
    const check = view.get("[data-test=home-orp-check]");
    expect(check.attributes("role")).toBe("checkbox");
    expect(check.attributes("aria-checked")).toBe("false");
    await check.trigger("click");
    expect(view.emitted("orp-check")).toEqual([[true]]);
    // Cochée : la ligne dit « Remis … », jamais de texte barré.
    const done = home({ orpDone: "2026-11-17T10:00:00" });
    expect(done.get("[data-test=todo-orp-urgent]").text()).toContain("Remis");
    expect(done.find("s, del").exists()).toBe(false);
    vi.restoreAllMocks();
  });

  it("ORP : la barre du mois, « Cette semaine » et « Voir le suivi »", () => {
    const view = home();
    expect(view.get("[data-test=home-band-orp] [data-test=month-count]").text()).toBe("7 sur 10");
    expect(view.get("[data-test=orp-bar-week]").text()).toContain("2 sur 3");
    expect(view.getComponent<typeof RouterLinkStub>("[data-test=home-orp]").props("to")).toBe("/bilan/orp");
  });

  it("Top du jour et les offres à trier : note, point « pas encore vue », raison surlignée, « Trier les offres »", () => {
    const view = home();
    expect(view.findAll("[data-test=home-top-offer]")).toHaveLength(1);
    expect(view.get("[data-test=home-top-offer] [data-test=score]").attributes("aria-label")).toBe("Très proche : 92 sur 100");
    expect(view.get("#home-sort-title").text()).toBe("1 offre à trier");
    const row = view.get("[data-test=home-card]");
    expect(row.find("[aria-label='Pas encore vue']").exists()).toBe(true);
    expect(row.get("mark").text()).toBe("Ansible");
    expect(view.getComponent<typeof RouterLinkStub>("[data-test=home-triage]").props("to")).toEqual({ name: "triage" });
  });

  it("sans offre à 75 ou plus, ni à trier : les deux feuilles sont absentes", () => {
    const view = home({ top: [], toSort: [] });
    expect(view.find("[data-test=home-top]").exists()).toBe(false);
    expect(view.find("[data-test=home-band-offers]").exists()).toBe(false);
  });

  it("sans titre à la main : le début du titre, ou « Bonjour » ; l’accroche du premier jour", () => {
    expect(home({ title: { lines: [], lead: "1 candidature", hand: "à envoyer.", sub: "" } }).get("h1").text()).toBe("1 candidature à envoyer.");
    const first = home({ firstDay: true, name: null, title: { lines: [], lead: "", hand: "", sub: "" } });
    expect(first.get("h1").text()).toBe("Bonjour.");
    expect(first.get("[data-test=home-tagline]").text()).toBe("Moins chercher,plus vivre.");
  });

  it("un jour de repos : « Si tu veux avancer »", () => {
    expect(home({ rest: true }).get("#home-todo-title").text()).toBe("Si tu veux avancer");
  });
});

describe("Le cercle liquide (D6)", () => {
  it("écrit toujours « x/y » et monte selon la part faite", () => {
    const circle = mount(LiquidCircle, { props: { count: 5, target: 10 } });
    expect(circle.find("text").text()).toBe("5/10");
    expect(circle.find("g[transform]").attributes("transform")).toBe("translate(0 50)");
  });
});

describe("Les feuilles empilées au défilement (§54 du 17.11)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("chaque feuille qui tient dans l’écran colle, à sa place dans la pile", async () => {
    const view = home();
    await nextTick();
    for (const key of ["home-todo", "home-band-orp", "home-top", "home-band-offers"]) expect(view.get(`[data-test=${key}]`).classes()).toContain("home-stick");
    expect(view.get("[data-test=home-top]").attributes("style")).toContain("--home-rank: 2");
  });

  it("une feuille plus haute que l’écran ne colle pas", async () => {
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(5000);
    const view = home();
    await nextTick();
    expect(view.find(".home-stick").exists()).toBe(false);
  });
});

describe("La scène des 4 personnages (§59 du 17.11)", () => {
  it("au-dessus du titre, 110 px de haut, décorative ; plus de visage à côté de « Rien à trier »", () => {
    const wrapper = home({ toSort: [] });
    const scene = wrapper.find(".home-hello > [data-illustration=troupe]");
    expect(scene.attributes("data-scene")).toBe("accueil-orp");
    expect(scene.attributes("height")).toBe("110");
    expect(scene.attributes("alt")).toBe("");
    expect(wrapper.find(".home-hello").element.firstElementChild).toBe(scene.element);
  });
});
