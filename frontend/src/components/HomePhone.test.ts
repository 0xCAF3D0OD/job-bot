// L'Accueil du téléphone (lot du 11 novembre au soir, PR 49 ; maquettes AccueilV2 et AccueilV2Sombre).
import { mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import type { Offer } from "../api/client";
import HomePhone from "./HomePhone.vue";

const offer = (id: number, score: number): Offer =>
  ({ id, title: `Poste ${id}`, company: "Alpstack", location: "Lausanne", score, rate_min: 80, rate_max: 100, employment_type: "CDI", has_logo: false }) as unknown as Offer;

const TODOS = [
  { key: "orp", test: "orp-urgent", title: "Remettre les justificatifs d’octobre", detail: "En retard depuis le 5 novembre", to: "/bilan/orp", late: true },
  { key: "preparing", test: "preparing", title: "Préparer 2 candidatures", detail: "2 offres gardées attendent leur lettre", to: "/candidatures/offres" },
  { key: "triage", test: "triage", title: "Trier 3 offres", detail: "La meilleure d’abord", to: { name: "triage" } },
];

function home(props: Partial<InstanceType<typeof HomePhone>["$props"]> = {}) {
  return mount(HomePhone, {
    props: { name: "Kevin", firstDay: false, month: "2026-11", count: 2, target: 10, offers: [offer(1, 78), offer(2, 60), offer(3, 55)], todos: TODOS, ...props },
    global: { stubs: { RouterLink: RouterLinkStub } },
  });
}

describe("L’Accueil du téléphone (AccueilV2, PR 49)", () => {
  it("bonjour, puis « À faire », la barre ORP et les offres à trier, dans cet ordre", () => {
    const view = home();
    expect(view.find("h1").text()).toBe("Bonjour Kevin.");
    expect(view.find("[data-test=home-tagline]").exists()).toBe(false);
    const html = view.html();
    const order = ["data-test=\"home-todo\"", "data-test=\"home-band-orp\"", "data-test=\"home-band-offers\""].map((t) => html.indexOf(t));
    expect(order.every((at, i) => at >= 0 && (i === 0 || at > order[i - 1]!))).toBe(true);
    // La barre ORP (PR 48) : le mois, le compte, ce qui reste et le rythme ; « Voir le suivi » mène au Bilan.
    const bar = view.find("[data-test=orp-bar]");
    expect(bar.text()).toContain("Mois ORP · novembre");
    expect(bar.find("[data-test=month-count]").text()).toBe("2 sur 10");
    expect(bar.find("[role=progressbar]").attributes("aria-valuenow")).toBe("2");
    expect(bar.find("[data-test=month-left]").text()).toMatch(/^Encore 8 d’ici le 5 décembre · (dans les temps|en retard)$/);
    expect(view.find("[data-test=home-orp]").text()).toBe("Voir le suivi");
  });

  it("les tâches sont numérotées ; celle en retard est la première, en brun ; toute la ligne est le lien", () => {
    const view = home();
    const rows = view.findAll("[data-test=home-todo] ol li a");
    expect(rows.map((r) => r.find(".home-todo-num").text())).toEqual(["1", "2", "3"]);
    expect(rows.map((r) => r.attributes("data-test"))).toEqual(["todo-orp-urgent", "todo-preparing", "todo-triage"]);
    expect(rows[0]!.classes()).toContain("home-todo-late");
    expect(rows[1]!.classes()).not.toContain("home-todo-late");
    expect(rows[0]!.find(".home-todo-text > b").text()).toBe("Remettre les justificatifs d’octobre");
    expect(rows[0]!.find(".home-todo-text > span").text()).toBe("En retard depuis le 5 novembre");
    // Le numéro est un dessin : la liste ordonnée le dit déjà aux lecteurs d'écran.
    expect(rows[0]!.find(".home-todo-num").attributes("aria-hidden")).toBe("true");
    expect(view.find("[data-test=home-todo] button").exists()).toBe(false);
  });

  it("un justificatif en retard : deux lignes à la main dans un seul titre, la phrase, le personnage décoratif", () => {
    const view = home({ late: { hand: "1 justificatif en retard,", then: "puis 2 candidatures", sub: "Commence par l’ORP : 2 minutes. Ensuite, ton rythme du jour." } });
    expect(view.findAll("h1")).toHaveLength(1);
    const hands = view.findAll("h1 .home-hand");
    expect(hands.map((h) => h.text())).toEqual(["1 justificatif en retard,", "puis 2 candidatures"]);
    expect(hands[0]!.classes()).toContain("home-hand-late");
    // Cinq mots au plus par ligne manuscrite (§1 du lot).
    for (const hand of hands) expect(hand.text().split(/\s+/).length).toBeLessThanOrEqual(5);
    expect(view.find(".home-late p").text()).toBe("Commence par l’ORP : 2 minutes. Ensuite, ton rythme du jour.");
    expect(view.find(".home-late img").attributes("alt")).toBe("");
    expect(view.text()).not.toContain("Bonjour");
  });

  it("l’entrée vers le tri : « {n} offres à trier », la meilleure offre en petite carte, « Trier les offres »", () => {
    const view = home();
    const band = view.find("[data-test=home-band-offers]");
    expect(band.find("h2").text()).toBe("3 offres à trier");
    expect(band.text()).toContain("La meilleure d’abord");
    const card = band.findAll("[data-test=home-card]");
    expect(card).toHaveLength(1);
    expect(card[0]!.find("b").text()).toBe("Poste 1");
    // Entreprise, lieu, puis le libellé de la note en minuscules.
    expect(card[0]!.find(".tri-peek-sub").findAll("span, b").map((x) => x.text())).toEqual(["Alpstack · Lausanne", "·", "proche"]);
    // La pile derrière la carte : deux bandes s'il reste au moins deux offres, une s'il en reste une, aucune sinon.
    expect(band.findAll(".tri-peek-pile")).toHaveLength(2);
    expect(home({ offers: [offer(1, 78), offer(2, 60)] }).findAll(".tri-peek-pile")).toHaveLength(1);
    expect(home({ offers: [offer(1, 78)] }).findAll(".tri-peek-pile")).toHaveLength(0);
    expect(home({ offers: [offer(1, 78)] }).find("[data-test=home-band-offers] h2").text()).toBe("1 offre à trier");
    const go = band.findComponent<typeof RouterLinkStub>("[data-test=home-triage]");
    expect(go.text()).toBe("Trier les offres");
    expect(go.props("to")).toEqual({ name: "triage" });
  });

  it("état vide : « Offres à trier », « Rien à trier pour l’instant », « Élargir ma recherche » vers les critères", () => {
    const view = home({ offers: [], widen: true, todos: TODOS.slice(0, 2) });
    const band = view.find("[data-test=home-band-offers]");
    expect(band.find("h2").text()).toBe("Offres à trier");
    expect(band.find("[data-test=home-card]").exists()).toBe(false);
    expect(band.find("[data-test=home-triage]").exists()).toBe(false);
    const none = band.find("[data-test=triage-none]");
    expect(none.find("b").text()).toBe("Rien à trier pour l’instant");
    expect(none.text()).toContain("jobA1 cherche chaque matin. Les prochaines offres arrivent demain.");
    expect(band.findComponent<typeof RouterLinkStub>("[data-test=triage-widen]").props("to")).toEqual({ path: "/reglages", query: { rubrique: "recherche" } });
    // La tâche « Trier » a disparu : les suivantes sont renumérotées.
    expect(view.findAll(".home-todo-num").map((n) => n.text())).toEqual(["1", "2"]);
    // Un jour de repos : la raison à la place, sans « Élargir ma recherche ».
    const rest = home({ offers: [], emptyTitle: "Jour de repos : rien à trier" });
    expect(rest.find("[data-test=triage-none] b").text()).toBe("Jour de repos : rien à trier");
    expect(rest.find("[data-test=triage-widen]").exists()).toBe(false);
  });

  it("l’accroche du premier jour, en français ; sans prénom, « Bonjour. » ; sans tâche, pas de bande « À faire »", () => {
    const view = home({ firstDay: true, name: null, todos: [] });
    expect(view.find("h1").text()).toBe("Bonjour.");
    expect(view.find("[data-test=home-tagline]").text()).toBe("Moins chercher,plus vivre.");
    expect(view.find("[data-test=home-todo]").exists()).toBe(false);
  });

  it("l’objectif atteint se dit", () => {
    expect(home({ count: 10 }).find("[data-test=month-left]").text()).toBe("Objectif atteint");
  });
});

describe("L’Accueil du téléphone : les bandes qui s’empilent (PR 36, dans l’ordre du 11 novembre)", () => {
  afterEach(() => vi.unstubAllGlobals());
  const motion = (reduce: boolean) =>
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: reduce && query.includes("reduce"), addEventListener() {}, removeEventListener() {} }));

  it("« À faire » et ORP collent quand elles tiennent dans l’écran ; les offres à trier ne collent jamais", async () => {
    motion(false);
    const view = home();
    await nextTick();
    expect(view.get("[data-test=home-todo]").classes()).toContain("home-stick");
    expect(view.get("[data-test=home-band-orp]").classes()).toContain("home-stick");
    expect(view.get("[data-test=home-band-offers]").classes()).not.toContain("home-stick");
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
