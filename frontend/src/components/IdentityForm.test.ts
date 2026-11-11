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
    expect(wrapper.find("[data-test=identity-phone]").attributes("placeholder")).toBe(" ");

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

describe("IdentityForm, « Pour les formulaires de candidature » (récapitulatif du 11 novembre, PR 44)", () => {
  const stubs = {
    BottomSheet: { props: ["open", "title", "subtitle", "icon"], template: "<div v-if=\"open\" data-test=\"sheet\"><h2>{{ title }}</h2><p class=\"sub\">{{ subtitle }}</p><slot /><slot name=\"actions\" /></div>" },
    BusyButton: { template: "<button type=\"submit\" form=\"answer-form\"><slot /></button>" },
    DateTimeField: true,
    DateTimePanel: true,
  };
  const IDENTITY = {
    name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null,
    linkedin: "https://www.linkedin.com/in/camille-exemple/", website: null, permit: "Permis C", availability: "2027-04-01", notice: null,
    salary: "95000", salary_mode: "auto",
  };
  async function mountWith(identity: Record<string, unknown>) {
    GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/identity" ? identity : undefined }));
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT);
    const wrapper = mount(IdentityForm, { global: { stubs }, attachTo: document.body });
    await flushPromises();
    return { wrapper, put };
  }

  it("cinq réponses comptées, « À compléter » en orange, « Site ou portfolio » facultatif et hors compte", async () => {
    const { wrapper } = await mountWith(IDENTITY);
    const section = wrapper.find("[data-test=identity-answers]");
    expect(section.find("h2").text()).toBe("Pour les formulaires de candidature");
    expect(section.find("[data-test=answers-count]").text()).toBe("4 réponses sur 5");
    expect(section.find("[data-test=answers-missing]").text()).toBe("Il en manque 1");
    const bar = section.find("[role=progressbar]");
    expect([bar.attributes("aria-valuenow"), bar.attributes("aria-valuemax")]).toEqual(["4", "5"]);
    expect(bar.findAll("span.on")).toHaveLength(4);
    expect(section.text()).toContain("jobA1 te les donne prêtes à copier quand un formulaire les demande.");
    const rows = section.findAll("li button");
    expect(rows.map((r) => r.find(".identity-answer-label").text())).toEqual([
      "Profil LinkedIn", "Permis de travail", "Disponible dès", "Délai de préavis", "Prétentions salariales", "Site ou portfolio",
    ]);
    expect(rows.every((r) => r.attributes("aria-haspopup") === "dialog")).toBe(true);
    expect(rows[0]!.find(".identity-answer-value").text()).toBe("linkedin.com/in/camille-exemple");
    expect(rows[2]!.find(".identity-answer-value").text()).toBe("1er avril 2027");
    expect(rows[3]!.find(".identity-answer-todo").text()).toBe("À compléter");
    expect(rows[4]!.find(".identity-answer-value").text()).toContain("95\u202F000 CHF brut par an");
    expect(rows[4]!.find("[data-icon=lock]").exists()).toBe(true);
    expect(rows[5]!.find(".identity-answer-optional").text()).toBe("Facultatif");
    expect(wrapper.find(".identity-ai").text()).toBe(
      "Ces informations servent à l’en-tête de tes lettres et aux formulaires de candidature. Elles ne sont jamais envoyées à l’IA.",
    );
    wrapper.unmount();
  });

  it("« Délai de préavis » : choisir « 2 mois », enregistrer ; la ligne se remplit et la progression disparaît à 5 sur 5", async () => {
    const { wrapper, put } = await mountWith(IDENTITY);
    put.mockResolvedValue({ data: { ...IDENTITY, notice: "2 mois" } } as never);
    await wrapper.find("[data-test=answer-notice]").trigger("click");
    const sheet = wrapper.find("[data-test=answer-sheet]");
    expect(sheet.find("h2").text()).toBe("Ton délai de préavis\u202F?");
    expect(sheet.text()).toContain("Le temps à respecter avant de quitter ton poste actuel.");
    const choices = sheet.findAll("[role=radiogroup] [role=radio]");
    expect(choices.map((c) => c.text())).toEqual(["Aucun", "1 mois", "2 mois", "3 mois", "Autre"]);
    await choices[2]!.trigger("click");
    expect(choices.map((c) => c.attributes("aria-checked"))).toEqual(["false", "false", "true", "false", "false"]);
    expect(choices[2]!.find("[data-icon=tick]").exists()).toBe(true);
    await sheet.find("[data-test=answer-form]").trigger("submit");
    await flushPromises();
    // Cette réponse seule part : les coordonnées en cours de saisie ne sont pas enregistrées avec.
    expect(put).toHaveBeenCalledWith("/api/identity", { body: { notice: "2 mois" } });
    expect(wrapper.find("[data-test=answer-sheet]").exists()).toBe(false);
    expect(wrapper.find("[data-test=answer-notice] .identity-answer-value").text()).toBe("2 mois");
    expect(wrapper.find("[data-test=answers-count]").exists()).toBe(false);
    expect(wrapper.find("[data-test=identity-answers] [role=progressbar]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("salaire illisible : « À compléter », le panneau rappelle l’ancienne saisie et ne l’efface pas sans montant", async () => {
    const { wrapper, put } = await mountWith({ ...IDENTITY, salary: "90 à 100k selon le poste", salary_mode: "auto" });
    put.mockResolvedValue({ data: { ...IDENTITY, salary: "90 à 100k selon le poste", salary_mode: "demander" } } as never);
    expect(wrapper.find("[data-test=answer-salary] .identity-answer-todo").text()).toBe("À compléter");
    expect(wrapper.find("[data-test=answers-count]").text()).toBe("3 réponses sur 5");
    await wrapper.find("[data-test=answer-salary]").trigger("click");
    const sheet = wrapper.find("[data-test=answer-sheet]");
    expect(sheet.find("h2").text()).toBe("Tes prétentions salariales\u202F?");
    expect(sheet.find("[data-test=answer-before]").text()).toBe("Tu avais écrit : « 90 à 100k selon le poste »");
    expect(sheet.text()).toContain("Visible seulement par toi. Utilisé seulement si un formulaire le demande, jamais envoyé à l’IA.");
    expect(sheet.find<HTMLInputElement>("[data-test=answer-mode-auto]").element.checked).toBe(true);
    await sheet.find("[data-test=answer-mode-demander]").setValue();
    await sheet.find("[data-test=answer-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenLastCalledWith("/api/identity", { body: { salary_mode: "demander" } });

    // Un montant : les milliers à l'espace fine, des chiffres seulement à l'enregistrement.
    put.mockResolvedValue({ data: { ...IDENTITY, salary: "98000", salary_mode: "demander" } } as never);
    await wrapper.find("[data-test=answer-salary]").trigger("click");
    const input = wrapper.find<HTMLInputElement>("[data-test=answer-input]");
    await input.setValue("98000");
    expect(input.element.value).toBe("98\u202F000");
    await wrapper.find("[data-test=answer-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenLastCalledWith("/api/identity", { body: { salary: "98000", salary_mode: "demander" } });
    expect(wrapper.find("[data-test=answer-salary] .identity-answer-value").text()).toContain("98\u202F000 CHF brut par an");
    wrapper.unmount();
  });

  it("LinkedIn : une adresse de profil attendue ; permis : une ancienne saisie libre s’ouvre sur « Autre »", async () => {
    const { wrapper, put } = await mountWith({ ...IDENTITY, permit: "Permis G (frontalier)" });
    await wrapper.find("[data-test=answer-linkedin]").trigger("click");
    expect(wrapper.find("[data-test=answer-sheet] h2").text()).toBe("Ton profil LinkedIn\u202F?");
    const input = wrapper.find<HTMLInputElement>("[data-test=answer-input]");
    expect(input.element.value).toBe("linkedin.com/in/camille-exemple");
    await input.setValue("camille-exemple");
    await wrapper.find("[data-test=answer-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Une adresse de profil, par exemple linkedin.com/in/ton-nom.");
    expect(put).not.toHaveBeenCalled();
    wrapper.unmount();

    const second = await mountWith({ ...IDENTITY, permit: "Permis G (frontalier)" });
    await second.wrapper.find("[data-test=answer-permit]").trigger("click");
    expect(second.wrapper.find("[role=radio][aria-checked=true]").text()).toBe("Autre");
    expect(second.wrapper.find<HTMLInputElement>("[data-test=answer-other]").element.value).toBe("Permis G (frontalier)");
    await second.wrapper.find("[data-test=answer-website]").exists();
    second.wrapper.unmount();
  });
});
