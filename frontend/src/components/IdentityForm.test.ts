import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import IdentityForm from "./IdentityForm.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn() },
  QUIET: { headers: { "X-Jobbot-Quiet": "1" } },
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
    expect(wrapper.find(".identity-message").text()).toContain("enregistrées");
  });

  it("remplit les champs vides avec les coordonnées repérées dans le CV, sans les enregistrer", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/identity"
            ? { name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null }
            : path === "/api/documents"
              ? [
                  { id: 9, kind: "certificate", text_status: "ok" },
                  { id: 4, kind: null, text_status: "ok" },
                ]
              : path === "/api/identity/from-document/{document_id}"
                ? { name: "Autre Nom", street: "Rue du Test 1", postcode: "1003", city: "Lausanne", phone: null, email: "camille@example.ch" }
                : undefined,
      }),
    );
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    // Le CV, pas le certificat ; le nom déjà saisi est gardé.
    expect(GET).toHaveBeenCalledWith("/api/identity/from-document/{document_id}", expect.objectContaining({ params: { path: { document_id: 4 } } }));
    const value = (test: string) => wrapper.find<HTMLInputElement>(`[data-test=identity-${test}]`).element.value;
    expect([value("name"), value("street"), value("postcode"), value("city"), value("email")]).toEqual([
      "Camille Exemple",
      "Rue du Test 1",
      "1003",
      "Lausanne",
      "camille@example.ch",
    ]);
    expect(put).not.toHaveBeenCalled();
    // Le bloc compte les champs réellement repris, chacun porte « Du CV » (PR 23) ; le nom saisi n'en a pas.
    expect(wrapper.find("[data-test=identity-from-cv]").text()).toContain("4 champs repris de ton CV");
    expect(wrapper.find("[data-test=identity-from-cv]").text()).toContain("Vérifie-les puis enregistre. Rien n’est enregistré avant.");
    const badges = () => wrapper.findAll(".form-field-badge").map((b) => b.element.closest("label")?.textContent?.replace("Du CV", "").trim());
    expect(badges()).toEqual(["E-mail", "Rue et numéro", "NPA", "Localité"]);
    // Une marque part dès que la valeur proposée est effacée.
    await wrapper.find("[data-test=identity-city]").setValue("");
    expect(wrapper.find("[data-test=identity-from-cv]").text()).toContain("3 champs repris");
    expect(wrapper.text()).toContain("Elles ne sont jamais envoyées à l’IA.");
    // « Annuler » vide les valeurs proposées et non enregistrées.
    const cancel = wrapper.findAll("button").find((b) => b.text() === "Annuler");
    expect(cancel).toBeDefined();
    await cancel!.trigger("click");
    expect(value("street")).toBe("");
    expect(wrapper.find("[data-test=identity-from-cv]").exists()).toBe(false);
    expect(wrapper.find(".form-field-badge").exists()).toBe(false);
  });

  it("l'e-mail du compte n'a pas de marque ; après « Enregistrer », les marques et le bloc partent", async () => {
    const { useAuth } = await import("../composables/useAuth");
    useAuth().me.value = { username: "kevin@example.ch" } as never;
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/documents"
            ? [{ id: 4, kind: null, text_status: "ok" }]
            : path === "/api/identity/from-document/{document_id}"
              ? { name: "Kevin Di Nocera", street: null, postcode: null, city: null, phone: "079 123 45 67", email: "autre@example.ch" }
              : undefined,
      }),
    );
    const { api } = await import("../api/client");
    vi.mocked(api.PUT).mockResolvedValue({ data: {} } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(wrapper.find<HTMLInputElement>("[data-test=identity-email]").element.value).toBe("kevin@example.ch");
    expect(wrapper.find("[data-test=identity-from-cv]").text()).toContain("2 champs repris de ton CV");
    expect(wrapper.find("[data-test=identity-email]").element.closest(".form-field")?.querySelector(".form-field-badge")).toBeNull();
    for (const [field, mode] of [["name", "name"], ["email", "email"], ["street", "street-address"], ["postcode", "postal-code"], ["city", "address-level2"], ["phone", "tel"]]) {
      expect(wrapper.find(`[data-test=identity-${field}]`).attributes("autocomplete")).toBe(mode);
    }
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=identity-from-cv]").exists()).toBe(false);
    expect(wrapper.find(".form-field-badge").exists()).toBe(false);
    useAuth().me.value = null;
  });

  it("sans CV lisible, le formulaire reste vide", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/documents" ? [{ id: 2, kind: null, text_status: "unreadable" }] : undefined }),
    );
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(GET).not.toHaveBeenCalledWith("/api/identity/from-document/{document_id}", expect.anything());
    expect(wrapper.find<HTMLInputElement>("[data-test=identity-street]").element.value).toBe("");
  });

  it("plateforme pas à jour : demande de la redémarrer", async () => {
    GET.mockResolvedValue({ data: undefined, response: { status: 404 } });
    const { api } = await import("../api/client");
    vi.mocked(api.PUT).mockResolvedValue({ data: undefined, response: { status: 404 } } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".identity-message").text()).toContain("redémarre-la");
  });
});

describe("IdentityForm, ce qui manque (docs/21 §6)", () => {
  it("annonce les champs manquants de l’en-tête", async () => {
    GET.mockResolvedValue({ data: { name: "Camille Exemple", street: null, postcode: null, city: "Lausanne", phone: null, email: null } });
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(wrapper.find("[data-test=identity-missing]").text()).toBe("Il manque\u202f: ta rue, ton NPA.");
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

  it("libellés de la maquette, erreur sous le champ et curseur dans le premier champ en erreur", async () => {
    GET.mockResolvedValue({ data: { name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null } });
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT);
    const wrapper = mount(IdentityForm, { attachTo: document.body });
    await flushPromises();
    const name = wrapper.find("[data-test=identity-name]");
    expect(wrapper.find(`label[for="${name.attributes("id")}"]`).text()).toBe("Prénom et nom");
    const phone = wrapper.find("[data-test=identity-phone]");
    expect(wrapper.find(`label[for="${phone.attributes("id")}"]`).text()).toBe("Téléphone");
    // Pas d’exemple en gris dans le champ : une espace seulement, pour le libellé flottant (PR 27).
    expect(wrapper.find("[data-test=identity-website]").attributes("placeholder")).toBe(" ");

    const postcode = wrapper.find("[data-test=identity-postcode]");
    await postcode.setValue("10");
    await postcode.trigger("blur");
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Quatre chiffres, par exemple 1020.");
    await wrapper.find("[data-test=identity-email]").setValue("camille@");
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(put).not.toHaveBeenCalled();
    expect(wrapper.findAll("[data-test=field-error]")).toHaveLength(2);
    // Le premier champ en erreur dans l'ordre de la maquette : l'e-mail, à côté du nom.
    expect(document.activeElement).toBe(wrapper.find("[data-test=identity-email]").element);
    expect(wrapper.find(".identity-message").exists()).toBe(false);

    // « Annuler » revient aux valeurs enregistrées.
    await wrapper.find("[data-test=cancel-identity]").trigger("click");
    expect(wrapper.find<HTMLInputElement>("[data-test=identity-postcode]").element.value).toBe("");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cancel-identity]").exists()).toBe(false);
    wrapper.unmount();
  });
});
