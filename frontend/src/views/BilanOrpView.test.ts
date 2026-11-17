// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { reactive, ref } from "vue";

import BilanOrpView from "./BilanOrpView.vue";

const GET = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn(), PUT: (...a: unknown[]) => PUT(...a), DELETE: (...a: unknown[]) => DELETE(...a) },
}));
const route = reactive<{ query: Record<string, string> }>({ query: {} });
const push = vi.fn();
vi.mock("vue-router", () => ({ useRoute: () => route, useRouter: () => ({ push: (...a: unknown[]) => push(...a) }) }));
vi.mock("../composables/usePhone", () => ({ usePhone: () => ({ phone: ref(true) }) }));
afterEach(() => GET.mockReset());

const row = (id: number, date: string, company: string, missing: string[] = []) => ({
  application_id: id,
  date,
  company,
  job_title: "DevOps Engineer",
  method: "électronique",
  missing,
});
const month = (target: number | null) => ({
  month: "2026-10",
  count: 4,
  target,
  rows: [row(1, "17.10.2026", "Vaud Network"), row(2, "28.10.2026", "Alpstack"), row(3, "24.10.2026", "Romandie Logistics", ["adresse"]), row(4, "21.10.2026", "Léman Data SA")],
  holder: { name: "Kevin", address: null },
  searches: [],
  changed_after_submit: false,
});
const week = { days: [], count: 0, target: 1 };

function mountView(target: number | null) {
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/orp" ? month(target) : { rhythm: week } }));
  return mount(BilanOrpView, {
    global: { stubs: { RouterLink: { props: ["to"], template: "<a><slot /></a>" }, OrpSheet: true } },
  });
}

function mountWith(data: ReturnType<typeof month>) {
  GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/orp" ? data : { rhythm: week } }));
  return mount(BilanOrpView, {
    global: { stubs: { RouterLink: { props: ["to"], template: "<a><slot /></a>" }, OrpSheet: true } },
  });
}

describe("Bilan › ORP sur téléphone (§37 du 16.11, planches OrpMois, OrpMoisPrecedents, OrpExports)", () => {
  afterEach(() => {
    route.query = {};
  });

  it("replié : la carte « Mois ORP · octobre » avec sa barre, les trois premières à déclarer en 2 lignes, sans phrase", async () => {
    const wrapper = mountView(10);
    await flushPromises();
    const goal = wrapper.find("[data-test=orp-goal]");
    expect(goal.find(".orp-month-band-head").text()).toBe("Mois ORP · octobre4 sur 10");
    expect(goal.find(".orp-month-band-bar > span").attributes("style")).toContain("width: 40%");
    // Sans date du serveur, le 5 du mois suivant (ORP_DEADLINE_DAY).
    expect(goal.find("[data-test=month-left]").text()).toBe("Encore 6 d’ici le 5 novembre");
    const declare = wrapper.find("[data-test=orp-to-declare]");
    expect(declare.find("h2").text()).toBe("À déclarer à l’ORP · 4");
    const cards = declare.findAll(".bilan-card");
    expect(cards).toHaveLength(3);
    expect(cards[0]!.find(".orp-phone-top > span").text()).toBe("Vaud Network");
    expect(cards[0]!.find(".bilan-card-what > span").text()).toBe("DevOps Engineer · 17 oct.");
    expect(cards[2]!.find(".orp-phone-chip.todo").text()).toBe("Infos à compléter");
    // Plus de « Afficher l'autre » ni de phrase sous les intertitres (règle de Kevin du 16.11) ; replié, pas de recherches.
    expect(wrapper.find("[data-test=orp-declare-more]").exists()).toBe(false);
    // (La feuille fermée des justificatifs, §58, a sa phrase : elle n'est pas sous un intertitre.)
    expect(wrapper.findAll("p").filter((p) => !p.element.closest("dialog"))).toHaveLength(0);
    expect(wrapper.find("[data-test=orp-searches]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-months]").text()).toBe("Mois précédents");
    expect(wrapper.find("[data-test=orp-exports]").text()).toBe("Autres exports");
  });

  it("« À déclarer à l’ORP » (§61 du 17.11) : le cercle coche la candidature, elle reste en place et le compteur baisse", async () => {
    PUT.mockResolvedValue({});
    DELETE.mockResolvedValue({});
    const wrapper = mountView(10);
    await flushPromises();
    const check = wrapper.get("[data-test=orp-declare-check-1]");
    expect(check.attributes("role")).toBe("checkbox");
    expect(check.attributes("aria-label")).toBe("Marquer Vaud Network comme déclarée");
    await check.trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}/job-room", { params: { path: { application_id: 1 } } });
    const declare = wrapper.get("[data-test=orp-to-declare]");
    expect(declare.get("h2").text()).toBe("À déclarer à l’ORP · 3");
    expect(declare.get("[data-test=orp-declare-check-1]").attributes("aria-checked")).toBe("true");
    expect(declare.get("[data-test=orp-declare-1] .bilan-card-what > span").text()).toMatch(/^Déclarée · \d+ \S+$/);
    expect(declare.find("s, del").exists()).toBe(false);
    await declare.get("[data-test=orp-declare-check-1]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/applications/{application_id}/job-room", { params: { path: { application_id: 1 } } });
    expect(wrapper.get("[data-test=orp-to-declare] h2").text()).toBe("À déclarer à l’ORP · 4");
  });

  it("déplié : toutes à déclarer, les recherches du mois avec leur pastille, puis « Replier le mois »", async () => {
    route.query = { tout: "1" };
    const data = month(10);
    data.rows = data.rows.map((r, i) => (i < 2 ? { ...r, declared_at: "2026-10-30" } : r)) as typeof data.rows;
    const wrapper = mountWith(data);
    await flushPromises();
    expect(wrapper.find("[data-test=orp-to-declare]").findAll(".bilan-card")).toHaveLength(2);
    const searches = wrapper.find("[data-test=orp-searches]");
    expect(searches.find(".bilan-section-head").text()).toBe("Recherches d’octobre4 ce mois");
    const rows = searches.findAll(".bilan-card");
    expect(rows).toHaveLength(2);
    expect(rows[0]!.find(".orp-phone-chip.ok").text()).toBe("Justificatif joint");
    expect(searches.find("[data-test=orp-fold]").text()).toBe("Replier le mois");
    await rows[0]!.trigger("click");
    expect(push).toHaveBeenCalledWith({ path: "/bilan/orp", query: { mois: "2026-10", candidature: 1 } });
  });

  it("« Autres exports » : le formulaire PDF, le CSV ; « Mois précédents » : les six derniers mois", async () => {
    const wrapper = mountView(10);
    await flushPromises();
    await wrapper.find("[data-test=orp-exports]").trigger("click");
    const exportsSheet = wrapper.find("[data-test=orp-exports-sheet]");
    expect(exportsSheet.findAll("li").map((l) => l.text())).toEqual(["Exporter le formulaire (PDF)", "Télécharger en CSV (Excel)"]);
    await wrapper.find("[data-test=orp-months]").trigger("click");
    expect(wrapper.find("[data-test=orp-months-sheet]").findAll("li")).toHaveLength(6);
  });

  it("sans objectif saisi : la phrase des Réglages, pas de « 0 sur 0 » ni de barre", async () => {
    const wrapper = mountView(null);
    await flushPromises();
    expect(wrapper.find(".orp-month-band-bar").exists()).toBe(false);
    expect(wrapper.find("[data-test=month-count]").text()).toBe("4");
    expect(wrapper.find("[data-test=month-left]").text()).toBe("Indique l’objectif fixé avec ton ORP dans les Réglages");
  });
});
