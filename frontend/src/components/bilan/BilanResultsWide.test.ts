// Bilan › Résultats sur ordinateur, en une colonne (récapitulatif du 11 novembre, PR 33 point 3 ; BilanOrdinateur).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import BilanResultsWide from "./BilanResultsWide.vue";

const GET = vi.fn();
vi.mock("../../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-11T10:00:00"));
});
afterEach(() => {
  GET.mockReset();
  vi.useRealTimers();
});

const group = (key: string, label: string, responses: number, total: number) => ({ key, label, responses, total, enough: total >= 5 });
const report = (applications = 26) => ({
  funnel: { received: 744, retained: 616, applications, responses: 0, interviews: 0, engagements: 0 },
  comparisons: [
    { key: "source", title: "", groups: [group("linkedin", "LinkedIn", 0, 11), group("indeed", "Indeed", 0, 12), group("manuel", "Ajoutée à la main", 1, 3)] },
    { key: "follow_up", title: "", groups: [] },
  ],
});
const meeting = {
  preparation: {
    months: [
      { month: "2026-10", count: 11, target: 13, answered: 0, interviews: 0 },
      { month: "2026-11", count: 4, target: 13, answered: 1, interviews: 0 },
    ],
  },
};
const today = { to_follow_up: 22, follow_ups: [{ sent_at: "2026-09-15T08:00:00Z" }, { sent_at: "2026-10-20T08:00:00Z" }] };

function serve(insights: unknown, day: unknown = today) {
  GET.mockImplementation((path: string) => {
    if (path === "/api/insights") return Promise.resolve({ data: insights });
    if (path === "/api/orp-meeting") return Promise.resolve({ data: meeting });
    if (path === "/api/today") return Promise.resolve({ data: day });
    return Promise.resolve({ data: undefined });
  });
}
async function mountWide() {
  const wrapper = mount(BilanResultsWide, {
    global: { stubs: { RouterLink: { props: ["to"], template: "<a :href=\"to\"><slot /></a>" }, FaceState: { props: ["title"], template: "<div>{{ title }}<slot /></div>" } } },
  });
  await flushPromises();
  return wrapper;
}

describe("Bilan › Résultats sur ordinateur", () => {
  it("une colonne : les chiffres des 3 mois, « Le mois en bref », « Ce qui bloque » ; plus de période ni de colonne de droite", async () => {
    serve(report());
    const wrapper = await mountWide();
    expect(GET).toHaveBeenCalledWith("/api/insights", { params: { query: { period: "recent" } } });
    expect(wrapper.findAll("[data-test=bilan-figures] li").map((li) => li.text())).toEqual(["26candidatures en 3 mois", "0réponse", "0entretien"]);
    expect(wrapper.findAll("h2").map((h) => h.text())).toEqual(["Le mois en bref", "Ce qui bloque"]);
    // Le mois en cours d'abord, avec l'objectif ORP.
    const months = wrapper.findAll("[data-test=bilan-months] li");
    expect(months.map((m) => m.find(".bilan-month-head").text())).toEqual(["Novembre 20264 sur 13", "Octobre 202611 sur 13"]);
    expect(months[0]!.find(".bilan-month-line").text()).toBe("1 réponse · 0 entretien");
    expect(months[1]!.find(".bilan-month-bar div").attributes("style")).toContain("width: 85%");
    expect(wrapper.find(".bilan-period").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Mois par mois");
    expect(wrapper.text()).not.toContain("Ce qui marche");
    expect(wrapper.emitted("ready")).toHaveLength(1);
  });

  it("« Ce qui bloque » : les réponses, les sites du plus fourni au moins fourni, les relances en attente et l’action", async () => {
    serve(report());
    const wrapper = await mountWide();
    const block = wrapper.get("[data-test=bilan-blocks]");
    expect(block.get(".bilan-section-head span").text()).toBe("sur 26 candidatures");
    expect(block.get("[data-test=bilan-block-responses]").text()).toBe("Réponses en 3 mois0");
    expect(block.get("[data-test=bilan-block-responses] strong").classes()).toContain("warn");
    expect(block.findAll("[data-test^=bilan-block-source-]").map((li) => li.text())).toEqual(["Indeed12 candidatures0 réponse", "LinkedIn11 candidatures0 réponse", "Ajoutée à la main3 candidatures1 réponse"]);
    expect(block.get("[data-test=bilan-block-waiting]").text()).toBe("Jamais relancéesLa plus ancienne attend depuis 57 jours22");
    const action = block.get("[data-test=bilan-block-action]");
    expect(action.text()).toBe("Relancer les 22 candidatures");
    expect(action.attributes("href")).toBe("/candidatures/suivi");
  });

  it("rien à relancer : ni la ligne ni l’action", async () => {
    serve(report(), { to_follow_up: 0, follow_ups: [] });
    const wrapper = await mountWide();
    expect(wrapper.find("[data-test=bilan-block-waiting]").exists()).toBe(false);
    expect(wrapper.find("[data-test=bilan-block-action]").exists()).toBe(false);
  });

  it("sans candidature : « Trop tôt pour conclure »", async () => {
    serve(report(0));
    const wrapper = await mountWide();
    expect(wrapper.get("[data-test=insights-empty]").text()).toContain("Trop tôt pour conclure");
    expect(wrapper.find("[data-test=bilan-blocks]").exists()).toBe(false);
  });
});
