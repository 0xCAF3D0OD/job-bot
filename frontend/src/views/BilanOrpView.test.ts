// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import BilanOrpView from "./BilanOrpView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn() } }));
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

describe("Bilan › ORP", () => {
  it("l'objectif, l'export, les trois dernières recherches et le lien, sans carte Semaine (A5 annulé)", async () => {
    const wrapper = mountView(10);
    await flushPromises();
    const goal = wrapper.find("[data-test=orp-goal]");
    expect(goal.find("[data-test=liquid-circle]").attributes("aria-label")).toBe("4 recherches sur 10");
    expect(goal.find("h2").text()).toBe("6 recherches à faire");
    expect(goal.find("p").text()).toBe("Objectif fixé avec ton ORP. Échéance le 31 octobre.");
    const rows = wrapper.findAll("[data-test=orp-rows] li");
    expect(rows.map((r) => r.find(".orp-what strong").text())).toEqual(["Alpstack", "Romandie Logistics", "Léman Data SA"]);
    expect(rows[0]!.text()).toContain("DevOps Engineer · Électronique");
    expect(rows.map((r) => r.find(".status-pill").text())).toEqual(["Preuve", "À joindre", "Preuve"]);
    // L'ordre de la page (B6).
    expect(wrapper.find("[data-test=rhythm]").exists()).toBe(false);
    expect(GET).not.toHaveBeenCalledWith("/api/today");
    const order = ["orp-goal", "orp-export", "orp-rows", "orp-all"].map((t) => wrapper.html().indexOf(`data-test="${t}"`));
    expect(order).toEqual([...order].sort((a, b) => a - b));
  });

  it("sans objectif saisi : la carte « Indique ton objectif ORP », pas de « 0 sur 0 »", async () => {
    const wrapper = mountView(null);
    await flushPromises();
    expect(wrapper.find("[data-test=liquid-circle]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-goal-missing] h2").text()).toBe("Indique ton objectif ORP");
  });
});
