// Le Bilan sur téléphone en feuilles empilées (LISEZMOI du 17.11, §52 et §54 ; planche BilanAccueil).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import BilanPhoneHome from "./BilanPhoneHome.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => GET.mockReset());

const now = new Date();
const thisMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
const row = (id: number, declared: string | null = null) => ({ application_id: id, date: "08.11.2026", company: "Alpstack", job_title: "SRE", method: "électronique", missing: [], declared_at: declared });
const orpMonth = (month: string, extra: Record<string, unknown> = {}) => ({
  month,
  count: 7,
  target: 10,
  due_date: null,
  state: "en_cours",
  rows: [row(1), row(2), row(3, "2026-11-10")],
  ...extra,
});

function mountHome({ lateMonth = true, responses = 3, training = true } = {}) {
  GET.mockImplementation((path: string, init?: { params?: { query?: { month?: string } } }) => {
    if (path === "/api/orp") {
      const asked = init?.params?.query?.month;
      if (!asked) return Promise.resolve({ data: orpMonth(thisMonth) });
      return Promise.resolve({ data: orpMonth(asked, { state: lateMonth ? "a_remettre" : "remis", rows: [row(9)] }) });
    }
    if (path === "/api/insights") return Promise.resolve({ data: { funnel: { applications: 14, responses, interviews: 1 } } });
    const items = training ? [{ id: 5, title: "AWS Solutions Architect", mark: { status: "in_progress", modules_done: 3, modules_total: 12 } }] : [];
    return Promise.resolve({ data: { items } });
  });
  return mount(BilanPhoneHome, { global: { stubs: { RouterLink: { props: ["to"], template: "<a :data-to=\"JSON.stringify(to)\"><slot /></a>" } } } });
}

describe("Bilan sur téléphone, feuilles empilées (§52, planche BilanAccueil)", () => {
  it("trois feuilles, chacune avec son lien vers le détail : ORP, Résultats, Formations", async () => {
    const wrapper = mountHome();
    await flushPromises();
    expect(wrapper.findAll("h2").map((h) => h.text())).toEqual(["ORP", "Résultats", "Formations"]);
    const link = (test: string) => wrapper.find(`[data-test=${test}]`);
    expect(link("bilan-orp-link").text()).toBe("Voir le suivi");
    expect(JSON.parse(link("bilan-orp-link").attributes("data-to")!)).toEqual({ path: "/bilan", query: { vue: "orp" } });
    expect(link("bilan-results-link").text()).toBe("Voir le détail");
    expect(JSON.parse(link("bilan-results-link").attributes("data-to")!)).toBe("/bilan/resultats");
    expect(link("bilan-trainings-link").text()).toBe("Catalogue");
    expect(JSON.parse(link("bilan-trainings-link").attributes("data-to")!)).toBe("/bilan/formations");
  });

  it("ORP : le mois, « 7 sur 10 », la ligne avec les recherches à déclarer, la pastille du mois à remettre", async () => {
    const wrapper = mountHome();
    await flushPromises();
    const name = new Intl.DateTimeFormat("fr-CH", { month: "long" }).format(now).toLowerCase();
    expect(wrapper.find("[data-test=bilan-sheet-orp]").text()).toContain(`Mois ORP · ${name}`);
    expect(wrapper.find("[data-test=bilan-orp-count]").text()).toBe("7 sur 10");
    // 2 du mois en cours (la 3e est déclarée) et 1 du mois passé, pas encore remis.
    expect(wrapper.find("[data-test=bilan-orp-line]").text()).toMatch(/^Encore 3 d’ici le .+ · 3 à déclarer$/);
    expect(wrapper.find("[data-test=bilan-orp-late]").text()).toMatch(/^\S+ à remettre$/);
  });

  it("le mois passé remis : ni pastille, ni ses recherches dans « à déclarer »", async () => {
    const wrapper = mountHome({ lateMonth: false });
    await flushPromises();
    expect(wrapper.find("[data-test=bilan-orp-late]").exists()).toBe(false);
    expect(wrapper.find("[data-test=bilan-orp-line]").text()).toMatch(/ · 2 à déclarer$/);
  });

  it("Résultats depuis le début : Envoyées, Réponses, Entretiens, et « 1 réponse sur 5 »", async () => {
    const wrapper = mountHome();
    await flushPromises();
    const rows = ["applications", "responses", "interviews"].map((key) => wrapper.find(`[data-test=bilan-funnel-${key}]`).text());
    expect(rows).toEqual(["Envoyées14", "Réponses3", "Entretiens1"]);
    expect(wrapper.find("[data-test=bilan-ratio]").text()).toBe("1 réponse sur 5");
    expect(wrapper.find("[data-test=bilan-sheet-results]").text()).toContain("depuis le début");
  });

  it("aucune réponse : pas de pastille ; aucune formation en cours : seulement la phrase", async () => {
    const wrapper = mountHome({ responses: 0, training: false });
    await flushPromises();
    expect(wrapper.find("[data-test=bilan-ratio]").exists()).toBe(false);
    expect(wrapper.find("[data-test=bilan-sheet-trainings]").text()).toBe("Formations Catalogue L’ORP peut financer une formation");
  });

  it("Formations : la formation en cours, son module", async () => {
    const wrapper = mountHome();
    await flushPromises();
    const text = wrapper.find("[data-test=bilan-sheet-trainings]").text();
    expect(text).toContain("AWS Solutions Architect");
    expect(text).toContain("Module 3 sur 12");
  });
});
