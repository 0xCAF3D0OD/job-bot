// Trier les offres (lot du 11 novembre au soir, PR 45) : une offre à la fois, « Écarter » et « Garder », la fin du tri.
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import TriageView from "./TriageView.vue";

const GET = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PATCH: (...a: unknown[]) => PATCH(...a) },
}));

const mounted: VueWrapper[] = [];
beforeEach(() => {
  localStorage.clear();
  PATCH.mockResolvedValue({ response: { ok: true } });
});
afterEach(async () => {
  await useUndo().flush();
  mounted.splice(0).forEach((w) => w.unmount());
  vi.resetAllMocks();
});

const offer = (id: number, title: string, score: number, more: Record<string, unknown> = {}) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne",
  score,
  employment_type: "CDI",
  rate_min: 80,
  rate_max: 100,
  description: "Vous exploitez nos clusters Kubernetes au quotidien.",
  snippet: null,
  passages: ["clusters Kubernetes"],
  strengths: [{ text: "Kubernetes : 40 services en production.", chunk_ids: [1] }, { text: "Terraform : Azure et AWS.", chunk_ids: [2] }, { text: "CI/CD : GitLab.", chunk_ids: [3] }],
  gaps: [{ text: "Allemand : demandé, à vérifier.", chunk_ids: [] }],
  keywords_asks: [],
  links: [],
  ...more,
});
// Un mois déjà atteint : jamais en retard, la dose reste à 3 quel que soit le jour où le test tourne.
const TODAY = { month_count: 10, month_target: 10, month: "2026-10", rhythm: { research_today: true } };

function mockApi(offers: unknown[], today: Record<string, unknown> = TODAY): void {
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/today" ? today : { items: offers } }));
}

async function mountTriage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/aujourdhui", name: "today", component: { template: "<div />" } },
      { path: "/candidatures/trier", name: "triage", component: TriageView },
      { path: "/candidatures/offres/:id/preparer", name: "preparation", component: { template: "<div />" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/candidatures/trier");
  // Dans un RouterView : la page envoie le dernier choix avant de laisser partir (onBeforeRouteLeave).
  const wrapper = mount({ template: "<RouterView />" }, { global: { plugins: [router] }, attachTo: document.body });
  mounted.push(wrapper);
  await flushPromises();
  return { wrapper, router };
}

describe("Trier les offres (PR 45)", () => {
  it("le titre, l’accroche, une offre à la fois dans une région nommée, le compteur une seule fois", async () => {
    mockApi([offer(1, "DevOps", 90), offer(2, "SRE", 80), offer(3, "Cloud", 75), offer(4, "Data", 70)]);
    const { wrapper } = await mountTriage();
    expect(wrapper.find("h1").text()).toBe("Trier les offres");
    // La dose du jour : 3 offres (5 si le mois est en retard), comme Aujourd'hui. Jamais un nombre en dur.
    expect(wrapper.find("[data-test=triage-count]").text()).toBe("3 offres pour toi");
    const region = wrapper.find("[data-test=triage-offer]");
    expect(region.attributes("aria-label")).toBe("Offre 1 sur 3");
    expect(wrapper.findAll("[data-test=triage-offer]")).toHaveLength(1);
    expect(wrapper.text().match(/1 sur 3/g)).toHaveLength(1);
    // L'ordre de lecture : titre, entreprise et lieu, note, étiquettes, extrait, points.
    const text = region.text();
    const order = ["DevOps", "Acme SA", "Très proche", "CDI", "clusters Kubernetes", "Kubernetes : 40 services"].map((t) => text.indexOf(t));
    expect(order.every((at, i) => at >= 0 && (i === 0 || at > order[i - 1]!))).toBe(true);
    expect(wrapper.find("[data-test=triage-tags]").text()).toContain("80–100 %");
  });

  it("l’extrait surligne les passages retrouvés, avec sa légende en texte ; trois points au plus, un seul à vérifier", async () => {
    mockApi([offer(1, "DevOps", 90)]);
    const { wrapper } = await mountTriage();
    const marks = wrapper.findAll("[data-test=triage-excerpt] mark");
    expect(marks.map((m) => m.text())).toEqual(["clusters Kubernetes"]);
    expect(wrapper.find("[data-test=triage-legend]").text()).toBe("1 point retrouvé");
    const points = wrapper.findAll("[data-test=triage-points] li");
    expect(points).toHaveLength(3);
    expect(points[2]!.text()).toContain("À vérifier : Allemand");
    // Un texte court tient en entier : pas de « Lire toute l’annonce ».
    expect(wrapper.find("[data-test=triage-read]").exists()).toBe(false);
  });

  it("sans passage retrouvé : ni surlignage ni légende, le début de l’annonce et « Lire toute l’annonce »", async () => {
    const long = "Notre entreprise familiale grandit chaque année depuis cinquante ans. ".repeat(12);
    mockApi([offer(7, "DevOps", 90, { passages: [], description: long })]);
    const { wrapper } = await mountTriage();
    expect(wrapper.find("[data-test=triage-excerpt] mark").exists()).toBe(false);
    expect(wrapper.find("[data-test=triage-legend]").exists()).toBe(false);
    expect(wrapper.find("[data-test=triage-excerpt]").text()).toContain("Notre entreprise familiale");
    expect(wrapper.find("[data-test=triage-read]").attributes("href")).toBe("/candidatures/offres?offre=7");
  });

  it("« Garder » et « Écarter » sont de vrais boutons avec leur raccourci ; le message, « Annuler », le focus", async () => {
    mockApi([offer(1, "DevOps", 90), offer(2, "SRE", 80)]);
    const { wrapper } = await mountTriage();
    const keep = wrapper.find("[data-test=triage-keep]");
    const dismiss = wrapper.find("[data-test=triage-dismiss]");
    expect([keep.element.tagName, keep.text(), keep.attributes("aria-keyshortcuts")]).toEqual(["BUTTON", "Garder", "ArrowRight"]);
    expect([dismiss.element.tagName, dismiss.text(), dismiss.attributes("aria-keyshortcuts")]).toEqual(["BUTTON", "Écarter", "ArrowLeft"]);
    // Sur ordinateur, les deux raccourcis sont affichés sous le compteur (touches dessinées).
    expect(wrapper.find("[data-test=triage-keys]").text().replace(/\s+/g, " ")).toBe("←Écarter→Garder");
    await keep.trigger("click");
    await flushPromises();
    const toast = wrapper.find("[data-test=triage-toast]");
    expect(toast.attributes("role")).toBe("status");
    expect(toast.text()).toContain("Offre gardée dans tes candidatures");
    // Le trait qui se vide pendant les 6 secondes : décoratif, caché des lecteurs d'écran.
    expect(toast.find(".tri-toast-bar").attributes("aria-hidden")).toBe("true");
    expect(wrapper.find("[data-test=triage-offer]").attributes("aria-label")).toBe("Offre 2 sur 2");
    expect(document.activeElement).toBe(wrapper.find("[data-test=triage-title]").element);
    // Rien n'est parti au serveur ; « Annuler » remet l'offre à l'écran.
    expect(PATCH).not.toHaveBeenCalled();
    await wrapper.find("[data-test=undo]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=triage-title]").text()).toBe("DevOps");
    expect(PATCH).not.toHaveBeenCalled();
    await dismiss.trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=triage-toast]").text()).toContain("Offre écartée");
  });

  it("trier 3 offres (garder, écarter, garder) : « 2 offres gardées, 1 écartée. », les deux offres, l’état « Gardée » en base", async () => {
    mockApi([offer(1, "DevOps", 90), offer(2, "SRE", 80), offer(3, "Cloud", 75)]);
    const { wrapper } = await mountTriage();
    for (const choice of ["keep", "dismiss", "keep"]) {
      await wrapper.find(`[data-test=triage-${choice}]`).trigger("click");
      await flushPromises();
    }
    const done = wrapper.find("[data-test=triage-done]");
    expect(done.find("h1").text().replace(/\s+/g, " ")).toBe("C’est trié !");
    expect(done.find("[data-test=triage-summary]").text()).toContain("2 offres gardées, 1 écartée.");
    const kept = done.findAll("[data-test=triage-kept] li");
    expect(kept.map((li) => li.find("b").text())).toEqual(["DevOps", "Cloud"]);
    expect(kept[0]!.find("a").attributes("href")).toBe("/candidatures/offres/1/preparer");
    expect(done.find("[data-test=triage-prepare-first]").attributes("href")).toBe("/candidatures/offres/1/preparer");
    expect(done.find("[data-test=triage-home]").attributes("href")).toBe("/aujourdhui");
    await useUndo().flush();
    const sent = PATCH.mock.calls.map((c) => [(c[1] as { params: { path: { offer_id: number } } }).params.path.offer_id, (c[1] as { body: { status: string } }).body.status]);
    expect(sent).toEqual([[1, "later"], [2, "ignored"], [3, "later"]]);
  });

  it("aucune offre gardée : pas de carte, la phrase et les prochaines offres, un seul bouton plein", async () => {
    mockApi([offer(1, "DevOps", 90)]);
    const { wrapper } = await mountTriage();
    await wrapper.find("[data-test=triage-dismiss]").trigger("click");
    await flushPromises();
    const done = wrapper.find("[data-test=triage-done]");
    expect(done.text()).toContain("Aucune offre gardée cette fois. Les prochaines offres arrivent demain matin.");
    expect(done.find("[data-test=triage-home]").classes()).toContain("tri-done-home-alone");
    expect(done.find("[data-test=triage-kept]").exists()).toBe(false);
    expect(done.find("[data-test=triage-prepare-first]").exists()).toBe(false);
    expect(done.findAll("a")).toHaveLength(1);
  });

  it("rien à trier, ou un jour de repos : un écran vide qui dit pourquoi", async () => {
    mockApi([]);
    const empty = (await mountTriage()).wrapper;
    expect(empty.find("[data-test=triage-empty]").text()).toContain("Rien à trier");
    mockApi([offer(1, "DevOps", 90)], { ...TODAY, rhythm: { research_today: false } });
    const rest = (await mountTriage()).wrapper;
    expect(rest.find("[data-test=triage-empty]").text()).toContain("Jour de repos");
  });
});
