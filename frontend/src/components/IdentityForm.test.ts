import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import IdentityForm from "./IdentityForm.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn() },
}));
afterEach(() => vi.resetAllMocks());

describe("IdentityForm", () => {
  it("charge et enregistre les coordonnées", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/identity"
            ? { name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null }
            : path === "/api/notifications"
              ? { configured: false, server: "https://ntfy.sh" }
              : { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 10 },
      }),
    );
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: {} } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    const name = wrapper.find<HTMLInputElement>("[data-test=identity-name]");
    expect(name.element.value).toBe("Camille Exemple");
    await wrapper.find("[data-test=identity-street]").setValue("Rue du Test 1");
    await wrapper.find("[data-test=identity-postcode]").setValue("1020");
    await wrapper.find("[data-test=identity-city]").setValue("Renens");
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/identity", {
      body: {
        name: "Camille Exemple",
        street: "Rue du Test 1",
        postcode: "1020",
        city: "Renens",
        phone: null,
        email: null,
        linkedin: null,
        website: null,
        availability: null,
        salary: null,
        permit: null,
      },
    });
    expect(wrapper.find("[data-test=identity-form] [role=status]").text()).toContain("enregistrées");
  });

  it("plateforme pas à jour : demande de la redémarrer", async () => {
    GET.mockResolvedValue({ data: undefined, response: { status: 404 } });
    const { api } = await import("../api/client");
    vi.mocked(api.PUT).mockResolvedValue({ data: undefined, response: { status: 404 } } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=identity-form] [role=status]").text()).toContain("redémarre-la");
  });
});

describe("IdentityForm, ce qui manque (docs/21 §6)", () => {
  it("annonce les champs manquants de l'en-tête", async () => {
    GET.mockResolvedValue({ data: { name: "Camille Exemple", street: null, postcode: null, city: "Lausanne", phone: null, email: null } });
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(wrapper.find("[data-test=identity-missing]").text()).toBe("Il manque : ta rue, ton NPA.");
  });
});

describe("IdentityForm, champs du formulaire (règles §4)", () => {
  it("des blocs gris sous le titre tant que les coordonnées chargent", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(wrapper.find("h2").text()).toBe("Coordonnées");
    expect(wrapper.find("[data-test=loading]").exists()).toBe(true);
    expect(wrapper.find("[data-test=identity-form]").exists()).toBe(false);
  });

  it("libellés reliés, « (facultatif) », erreur sous le champ et curseur dans le premier champ en erreur", async () => {
    GET.mockResolvedValue({ data: { name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null } });
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT);
    const wrapper = mount(IdentityForm, { attachTo: document.body });
    await flushPromises();
    const name = wrapper.find("[data-test=identity-name]");
    expect(wrapper.find(`label[for="${name.attributes("id")}"]`).text()).toBe("Nom et prénom");
    const phone = wrapper.find("[data-test=identity-phone]");
    expect(wrapper.find(`label[for="${phone.attributes("id")}"]`).text()).toBe("Téléphone (facultatif)");
    expect(wrapper.find("[data-test=identity-website]").attributes("placeholder")).toBeUndefined();

    const postcode = wrapper.find("[data-test=identity-postcode]");
    await postcode.setValue("10");
    await postcode.trigger("blur");
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Quatre chiffres, par exemple 1020.");
    await wrapper.find("[data-test=identity-email]").setValue("camille@");
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(put).not.toHaveBeenCalled();
    expect(wrapper.findAll("[data-test=field-error]")).toHaveLength(2);
    expect(document.activeElement).toBe(postcode.element);
    expect(wrapper.find("[data-test=identity-form] [role=status]").exists()).toBe(false);

    // « Annuler » revient aux valeurs enregistrées.
    await wrapper.find("[data-test=cancel-identity]").trigger("click");
    expect(wrapper.find<HTMLInputElement>("[data-test=identity-postcode]").element.value).toBe("");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cancel-identity]").exists()).toBe(false);
    wrapper.unmount();
  });
});
