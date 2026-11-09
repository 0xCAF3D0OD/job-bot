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

describe("Bilan › ORP sur téléphone, en blocs (lot 18, §10.2)", () => {
  it("l'objectif et la date de remise, « À déclarer à l'ORP » vers la fiche, « Recherches du mois » et l'export", async () => {
    const wrapper = mountView(10);
    await flushPromises();
    const goal = wrapper.find("[data-test=orp-goal]");
    expect(goal.find("[data-test=liquid-circle]").attributes("aria-label")).toBe("4 recherches sur 10");
    expect(goal.find(".block-cap").text()).toBe("Octobre");
    // Maquette du 9 novembre (§11) : sans date du serveur, le 5 du mois suivant (ORP_DEADLINE_DAY) ; plus de note
    // sur la conseillère.
    expect(goal.find("h2").text()).toBe("Encore 6 d’ici le 5 novembre");
    expect(goal.find("[data-test=orp-deadline]").exists()).toBe(false);
    // Aucune n'est déclarée : quatre à déclarer, trois montrées, « Afficher l'autre ».
    const declare = wrapper.find("[data-test=orp-to-declare]");
    expect(declare.find("h2").text()).toBe("À déclarer à l’ORP · 4");
    const rows = declare.findAll(".block-row");
    expect(rows).toHaveLength(3);
    expect(rows[0]!.find(".block-row-title").text()).toBe("Vaud Network");
    expect(rows[0]!.findAll(".block-row-line").map((l) => l.text())).toEqual([", DevOps Engineer · En ligne", ", Envoyée le 17 octobre"]);
    expect(rows[2]!.find(".block-status").text()).toBe(", infos à compléter");
    expect(rows[0]!.find(".arrow-circle").attributes("aria-hidden")).toBe("true");
    await declare.find("[data-test=orp-declare-more]").trigger("click");
    expect(declare.findAll(".block-row")).toHaveLength(4);
    const searches = wrapper.find("[data-test=orp-searches]");
    expect(searches.find("h2").text()).toBe("Recherches du mois · 0");
    expect(searches.find("[data-test=orp-proof-note]").text()).toBe("L’ORP peut demander un justificatif pour chaque recherche : l’e-mail de confirmation ou une capture.");
    expect(searches.find("[data-test=orp-export]").text()).toBe("Exporter le formulaire (PDF)");
    expect(searches.find("[data-test=orp-export]").classes()).toContain("action-2");
  });

  it("sans objectif saisi : « Indique ton objectif ORP », pas de « 0 sur 0 »", async () => {
    const wrapper = mountView(null);
    await flushPromises();
    expect(wrapper.find("[data-test=liquid-circle]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-goal] h2").text()).toBe("Indique ton objectif ORP");
  });
});
