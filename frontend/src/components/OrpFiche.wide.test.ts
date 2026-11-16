// « Pour l'ORP » dans le panneau du Bilan sur ordinateur (maquette du 13.11, BilanOrdinateurFiche).
import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import OrpFiche from "./OrpFiche.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn() } }));
afterEach(() => GET.mockReset());

const field = (label: string, value: string, choice = false) => ({ step: "", label, value, choice });
const row = (extra: Record<string, unknown> = {}) => ({
  application_id: 3,
  date: "22.10.2026",
  company: "Qim info",
  job_title: "Ingénieur DevOps",
  method: "électronique",
  result: "en suspens",
  missing: ["adresse de l'entreprise"],
  declared_at: null,
  job_room: [
    field("Date", "22.10.2026"),
    field("Mode", "Par voie électronique", true),
    field("Entreprise", "Qim info SA"),
    field("Rue", ""),
    field("N°", ""),
    field("Numéro de case postale", ""),
    field("Pays", "Suisse", true),
    field("NPA / Lieu", "1204 Genève"),
    field("Personne contactée", ""),
    field("Désignation du poste", "Ingénieur DevOps"),
    field("Lien vers le formulaire en ligne", "https://www.linkedin.com/jobs/view/4480047691/"),
  ],
  ...extra,
});

async function mountFiche(data = row(), wide = true) {
  GET.mockResolvedValue({ data: { rows: [data] } });
  const wrapper = mount(OrpFiche, { props: { applicationId: 3, month: "2026-10", wide }, global: { stubs: { RouterLink: RouterLinkStub } } });
  await flushPromises();
  return wrapper;
}
const labels = (wrapper: Awaited<ReturnType<typeof mountFiche>>) =>
  wrapper.findAll("[data-test=copy-field]").map((f) => f.find(".block-field-label").text());

describe("OrpFiche sur ordinateur (wide)", () => {
  it("la candidature en deux lignes, sans les blocs « Candidature » et « Déclarer dans Job-Room »", async () => {
    const wrapper = await mountFiche();
    expect(wrapper.get("[data-test=orp-fiche-who] strong").text()).toBe("Qim info");
    expect(wrapper.get("[data-test=orp-fiche-sent]").text()).toBe("Ingénieur DevOps · envoyée le 22 octobre");
    expect(wrapper.find("[data-test=orp-fiche-job-room]").exists()).toBe(false);
    expect(wrapper.find(".block").exists()).toBe(false);
  });

  it("l'adresse manque : l'encadré le dit ; sinon pas d'encadré", async () => {
    let wrapper = await mountFiche();
    expect(wrapper.get("[data-test=orp-fiche-address-missing]").text()).toBe(
      "Il manque l’adresse de l’entrepriseL’ORP la demande. Complète-la ci-dessous avant de déclarer.",
    );
    wrapper = await mountFiche(row({ missing: [] }));
    expect(wrapper.find("[data-test=orp-fiche-address-missing]").exists()).toBe(false);
  });

  it("les lignes de la planche : lien de l'annonce, « Rue et numéro », personne contactée seule, étiquette sans case", async () => {
    const wrapper = await mountFiche();
    expect(labels(wrapper)).toEqual(["Date", "Mode", "Poste", "Lien de l’annonce", "Nom", "Rue et numéro", "NPA et lieu", "Pays", "Personne contactée"]);
    expect(wrapper.get(".block-tick").text()).toBe("Case à cocher dans Job-Room");
  });

  it("« Compléter » à côté de la rue manquante : la candidature à modifier, sur l'adresse (comme « Ajouter », §8)", async () => {
    let wrapper = await mountFiche();
    const link = wrapper.getComponent(RouterLinkStub);
    expect(link.attributes("data-test")).toBe("orp-fiche-complete");
    expect(link.props("to")).toEqual({ path: "/candidatures/suivi", query: { candidature: "3", modifier: "adresse" } });
    expect(link.text()).toBe("Compléter l’adresse de l’entreprise");
    expect(wrapper.get("[data-test=orp-fiche-declare]").attributes("disabled")).toBeUndefined();
    wrapper = await mountFiche(row({ missing: [] }));
    expect(wrapper.find("[data-test=orp-fiche-complete]").exists()).toBe(false);
  });

  it("la phrase du bas nomme le mois de la recherche", async () => {
    const wrapper = await mountFiche();
    expect(wrapper.get("[data-test=orp-fiche-note]").text()).toBe("Elle passe dans « Recherches d’octobre ».");
  });

  it("téléphone et détail d'une envoyée (sans wide) : inchangés", async () => {
    const wrapper = await mountFiche(row(), false);
    expect(wrapper.find("[data-test=orp-fiche-who]").exists()).toBe(false);
    expect(wrapper.find("[data-test=orp-fiche-job-room]").exists()).toBe(true);
    expect(labels(wrapper)).not.toContain("Lien de l’annonce");
    expect(labels(wrapper)).toContain("Rue et n°");
    expect(wrapper.get(".block-tick").text()).toBe("☐ case à cocher dans Job-Room");
    expect(wrapper.get("[data-test=orp-fiche-note]").text()).toBe("Elle passe dans « Recherches du mois ».");
  });
});
