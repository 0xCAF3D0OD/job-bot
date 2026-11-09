// « Pour l'ORP », une candidature à déclarer (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OrpFicheView from "./OrpFicheView.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) } }));
afterEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

const field = (label: string, value: string, choice = false) => ({ step: "", label, value, choice });
const row = {
  application_id: 7,
  date: "29.10.2026",
  company: "SpeciTec SA",
  job_title: "IT Tooling / DevOps Specialist",
  method: "électronique",
  result: "en suspens",
  missing: [],
  declared_at: null,
  job_room: [
    field("Date", "29.10.2026"),
    field("Mode", "Par voie électronique", true),
    field("Entreprise", "SpeciTec SA"),
    field("Rue", "Place de Pont-Rouge"),
    field("N°", "1"),
    field("Numéro de case postale", ""),
    field("Pays", "Suisse", true),
    field("NPA / Lieu", "1212 Grand-Lancy"),
    field("Personne contactée", ""),
    field("Désignation du poste", "IT Tooling / DevOps Specialist"),
  ],
};

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/bilan/orp/candidature/:id", component: OrpFicheView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/bilan/orp/candidature/7?mois=2026-10");
  GET.mockResolvedValue({ data: { rows: [row] } });
  const wrapper = mount(OrpFicheView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("OrpFicheView", () => {
  it("les champs à recopier (D32) : libellé au-dessus, copier, cases à cocher, « Non renseigné »", async () => {
    const { wrapper } = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-10" } } });
    expect(wrapper.find("h1").text()).toBe("Pour l’ORP");
    expect(wrapper.find("[data-test=orp-fiche-sent]").text()).toMatch(/^Envoyée le 29 octobre · sans réponse depuis \d+ jours$/);
    const fields = wrapper.findAll("[data-test=copy-field]").map((f) => [f.find(".block-field-label").text(), f.find(".block-field-value").text()]);
    expect(fields).toEqual([
      ["Date", "29.10.2026"],
      ["Mode", "Par voie électronique"],
      ["Poste", "IT Tooling / DevOps Specialist"],
      ["Nom", "SpeciTec SA"],
      ["Rue et n°", "Place de Pont-Rouge 1"],
      ["NPA et lieu", "1212 Grand-Lancy"],
      ["Pays", "Suisse"],
      ["Case postale · Personne contactée", "Non renseigné"],
    ]);
    const mode = wrapper.findAll("[data-test=copy-field]")[1]!;
    expect(mode.find(".block-tick").text()).toBe("☐ case à cocher dans Job-Room");
    expect(mode.find("[data-test=field-copy]").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=copy-field]")[0]!.find("[data-label='Copier']").text()).toBe("Copier : date");
    const jobRoom = wrapper.find("[data-test=orp-fiche-job-room]");
    expect(jobRoom.attributes("target")).toBe("_blank");
    expect(jobRoom.classes()).toContain("action-2");
  });

  it("« Marquer comme déclarée » (niveau 1) enregistre puis revient au Suivi ORP", async () => {
    const { wrapper, router } = await mountView();
    PUT.mockResolvedValue({ response: { status: 204 } });
    const button = wrapper.find("[data-test=orp-fiche-declare]");
    expect(button.classes()).toContain("action-1");
    await button.trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/applications/{application_id}/job-room", { params: { path: { application_id: 7 } } });
    expect(router.currentRoute.value.fullPath).toBe("/bilan/orp?mois=2026-10");
  });
});
