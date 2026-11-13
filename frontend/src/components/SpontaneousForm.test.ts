import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import SpontaneousForm from "./SpontaneousForm.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

describe("Candidature spontanée (docs/39)", () => {
  it("crée la candidature, propose l’adresse au registre, puis ouvre la préparation", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/candidatures/offres");
    POST.mockResolvedValueOnce({ data: { id: 77 } });
    // La recherche au registre est une écriture (docs/78 §2).
    POST.mockResolvedValueOnce({
      data: { candidates: [{ uid: "CHE-1", name: "Exemple SA", address: "Rue 1\n1000 Lausanne", canton: "VD" }], web_address: null },
    });
    POST.mockResolvedValueOnce({ data: { company_address: "Rue 1\n1000 Lausanne", company_address_source: "registry" } });
    const wrapper = mount(SpontaneousForm, { global: { plugins: [router] } });
    // Maquette CandidaturesOrdinateurSpontanee (PR 38) : la phrase, trois champs, « Pourquoi » facultatif.
    expect(wrapper.find("[data-test=spontaneous-lead]").text()).toBe("Pour une entreprise qui n’a pas publié d’offre. jobA1 prépare une lettre et un CV adaptés.");
    expect(wrapper.findAll(".form-field-label").map((l) => l.text())).toEqual(["Entreprise", "Poste visé", "Pourquoi cette entreprise\u202f? (facultatif)"]);
    expect(wrapper.findAll(".form-field-hint").map((l) => l.text())).toEqual([
      "Par exemple\u202f: Ingénieur DevOps",
      "Ce qui t’attire\u202f: produit, équipe, valeurs. jobA1 s’en sert pour la lettre.",
    ]);

    await wrapper.find("[data-test=spontaneous-company]").setValue("Exemple SA");
    await wrapper.find("[data-test=spontaneous-title]").setValue("Ingénieur DevOps");
    await wrapper.find("[data-test=spontaneous-reason]").setValue("Leur plateforme cloud.");
    await wrapper.find("[data-test=spontaneous-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body).toEqual({
      company: "Exemple SA",
      title: "Ingénieur DevOps",
      reason: "Leur plateforme cloud.",
      force: false,
    });
    // La liste des offres se recharge dès la création, même sans passer par « Préparer ».
    expect(wrapper.emitted("created")).toEqual([[77]]);

    await wrapper.find("[data-test=spontaneous-search]").trigger("click");
    await flushPromises();
    await wrapper.find("[data-test=spontaneous-choose]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=spontaneous-chosen]").text()).toContain("Rue 1, 1000 Lausanne");

    await wrapper.find("[data-test=spontaneous-prepare]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/candidatures/offres/77/preparer");
  });

  it("une offre chez cette entreprise est déjà là : l’avis l’ouvre, ou « Créer quand même »", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    POST.mockResolvedValueOnce({ data: { id: null, existing: { id: 12, title: "Technicien", company: "SpeciTec SA", spontaneous: false } } });
    POST.mockResolvedValueOnce({ data: { id: 78 } });
    const wrapper = mount(SpontaneousForm, { global: { plugins: [router] } });
    await wrapper.find("[data-test=spontaneous-company]").setValue("SpeciTec");
    await wrapper.find("[data-test=spontaneous-title]").setValue("Dessinateur");
    await wrapper.find("[data-test=spontaneous-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=spontaneous-existing]").text()).toContain("Tu as déjà une offre chez SpeciTec SA : « Technicien ».");
    expect(wrapper.emitted("created")).toBeUndefined();
    await wrapper.find("[data-test=spontaneous-open-existing]").trigger("click");
    expect(wrapper.emitted("open")).toEqual([[12]]);
    expect(wrapper.find("[data-test=spontaneous-create]").text()).toBe("Créer quand même");
    await wrapper.find("[data-test=spontaneous-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[1]![1].body.force).toBe(true);
    expect(wrapper.emitted("created")).toEqual([[78]]);
  });

  it("dans le panneau « Ajouter » : pas de bouton dans le formulaire, le pied l’envoie ; « Pourquoi » peut rester vide", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    POST.mockResolvedValueOnce({ data: { id: 79 } });
    const wrapper = mount(SpontaneousForm, { props: { formId: "add-spontaneous-form" }, global: { plugins: [router] } });
    expect(wrapper.find("form").attributes("id")).toBe("add-spontaneous-form");
    expect(wrapper.find("[data-test=spontaneous-create]").exists()).toBe(false);
    const exposed = wrapper.vm as unknown as { label: string; created: boolean };
    expect(exposed.label).toBe("Créer la candidature");
    await wrapper.find("[data-test=spontaneous-company]").setValue("Exemple SA");
    await wrapper.find("[data-test=spontaneous-title]").setValue("Menuisier");
    await wrapper.find("[data-test=spontaneous-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body).toEqual({ company: "Exemple SA", title: "Menuisier", reason: "", force: false });
    expect(exposed.created).toBe(true);
    expect(exposed.label).toBe("Préparer la candidature");
    expect(wrapper.find("[data-test=spontaneous-prepare]").exists()).toBe(false);
  });
});
