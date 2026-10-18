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
  it("crée la candidature, propose l'adresse au registre, puis ouvre la préparation", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/candidatures/offres");
    POST.mockResolvedValueOnce({ data: { id: 77 } });
    // La recherche au registre est une écriture (docs/78 §2).
    POST.mockResolvedValueOnce({
      data: { candidates: [{ uid: "CHE-1", name: "Exemple SA", address: "Rue 1\n1000 Lausanne", canton: "VD" }], web_address: null },
    });
    POST.mockResolvedValueOnce({ data: { company_address: "Rue 1\n1000 Lausanne", company_address_source: "registry" } });
    const wrapper = mount(SpontaneousForm, { global: { plugins: [router] } });

    await wrapper.find("[data-test=spontaneous-company]").setValue("Exemple SA");
    await wrapper.find("[data-test=spontaneous-title]").setValue("Ingénieur DevOps");
    await wrapper.find("[data-test=spontaneous-reason]").setValue("Leur plateforme cloud.");
    await wrapper.find("[data-test=spontaneous-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body).toEqual({
      company: "Exemple SA",
      title: "Ingénieur DevOps",
      reason: "Leur plateforme cloud.",
      website: null,
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
});
