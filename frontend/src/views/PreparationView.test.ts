import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import PreparationView from "./PreparationView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const offer = {
  id: 7,
  title: "Ingénieur DevOps junior",
  company: "Acme SA",
  location: "Lausanne, VD",
  status: "to_review",
  apply_url: "https://acme.example/jobs/1",
  apply_kind: "external",
  links: [],
};

function letter(id: number, version: number, extra: Record<string, unknown> = {}) {
  return {
    id,
    offer_id: 7,
    version,
    language: "fr",
    subject: "Candidature au poste d'ingénieur DevOps junior",
    paragraphs: [
      { text: "Votre annonce a retenu mon attention.", chunk_ids: [] },
      { text: "J'administre un cluster K3s.", chunk_ids: [1] },
    ],
    employer: { address: null, contact_name: null, contact_phone: null },
    instruction: null,
    model: "claude-opus-5",
    created_at: `2026-10-05T0${version}:00:00Z`,
    edited_at: null,
    document: {
      language: "fr",
      sender: ["Camille Exemple", "Rue du Test 1", "1020 Renens"],
      place_date: "Renens, le 5 octobre 2026",
      recipient: ["Acme SA"],
      subject_line: "Objet : Candidature au poste d'ingénieur DevOps junior",
      salutation: "Madame, Monsieur,",
      paragraphs: [],
      closing: "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.",
      signature: "Camille Exemple",
      enclosure: "Annexe : curriculum vitae",
      missing_identity: [],
    },
    ...extra,
  };
}

function mockGet(letters: unknown[]): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/offers/{offer_id}"
          ? offer
          : path === "/api/offers/{offer_id}/letters"
            ? letters
            : [{ id: 1, title: "Kubernetes" }],
    }),
  );
}

async function mountView(path = "/offres/7/preparer") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/offres/:id/preparer", component: PreparationView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(PreparationView, { global: { plugins: [router], stubs: { ContactsPanel: true, FormSheet: true } } });
  await flushPromises();
  return wrapper;
}

describe("PreparationView", () => {
  it("sans lettre : propose de la rédiger, puis affiche la lettre assemblée", async () => {
    mockGet([]);
    POST.mockResolvedValue({ data: letter(11, 1) });
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=no-letter]").exists()).toBe(true);
    expect(wrapper.find("[data-test=instruction]").exists()).toBe(false);

    await wrapper.find("[data-test=language]").setValue("fr");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/letters", {
      params: { path: { offer_id: 7 } },
      body: { language: "fr", instruction: null, base_draft_id: null },
    });
    const sheet = wrapper.find("[data-test=letter]");
    expect(sheet.text()).toContain("Renens, le 5 octobre 2026");
    expect(sheet.text()).toContain("Objet :");
    expect(sheet.text()).toContain("Blocs : Kubernetes");
    expect(wrapper.find<HTMLInputElement>("[data-test=subject]").element.value).toBe(
      "Candidature au poste d'ingénieur DevOps junior",
    );
    expect(wrapper.find("[data-test=docx]").attributes("href")).toBe("/api/letters/11/docx");
    expect(wrapper.find("[data-test=pdf]").attributes("href")).toBe("/api/letters/11/pdf");
  });

  it("la version modifiée en dernier est celle affichée ; les corrections s'enregistrent", async () => {
    mockGet([letter(12, 2), letter(11, 1, { edited_at: "2026-10-05T09:00:00Z" })]);
    PUT.mockResolvedValue({ data: letter(11, 1, { subject: "Candidature", edited_at: "2026-10-05T10:00:00Z" }) });
    const wrapper = await mountView();
    expect(wrapper.findAll("[data-test=version]")).toHaveLength(2);
    // La version affichée est marquée (pastille de sélection, aria-current).
    expect(wrapper.find(".versions [aria-current=page]").text()).toContain("v1");

    await wrapper.find("[data-test=subject]").setValue("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(false);
    await wrapper.find("[data-test=save-letter]").trigger("click");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { params: unknown; body: { subject: string } }];
    expect(path).toBe("/api/letters/{draft_id}");
    expect(opts.body.subject).toBe("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(true);
  });

  it("une consigne longue : six mots pour nom, la consigne entière au-dessus de la lettre, sans « … »", async () => {
    const long = "Insiste davantage sur Kubernetes et Terraform, raccourcis ".repeat(6).trim();
    expect(long.length).toBeGreaterThan(300);
    mockGet([letter(12, 2, { instruction: long }), letter(11, 1)]);
    const wrapper = await mountView();
    const versions = wrapper.findAll("[data-test=version]");
    const named = versions.find((v) => v.text().includes("Insiste"))!;
    expect(named.find(".grouped-row-title").text()).toBe("Insiste davantage sur Kubernetes et Terraform");
    expect(named.text()).not.toContain("…");
    expect(versions.some((v) => v.find(".grouped-row-title").text() === "Première rédaction")).toBe(true);
    // La consigne entière s'affiche aussi au-dessus de la lettre de la version choisie.
    await named.trigger("click");
    expect(wrapper.find("[data-test=version-instruction]").text()).toBe(`Consigne : ${long}`);
    // La consigne a son libellé (FormField), le bouton dit ce qu'il fait.
    expect(wrapper.find("label[for]").exists()).toBe(true);
    expect(wrapper.find("[data-test=write]").text()).toContain("Rédiger la nouvelle version");
  });

  it("nouvelle version avec consigne : part de la version affichée", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({ data: letter(12, 2, { instruction: "plus court" }) });
    const wrapper = await mountView();
    await wrapper.find("[data-test=instruction]").setValue("plus court");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toEqual({ language: null, instruction: "plus court", base_draft_id: 11 });
    expect(wrapper.find(".versions [aria-current=page] .grouped-row-title").text()).toBe("Plus court");
  });

  it("la lettre s'affiche relue : « Relue : 6/7 », le détail avec ses pastilles, « Relecture… »", async () => {
    mockGet([letter(11, 1)]);
    const criteria = [
      ["accroche", "Accroche", true],
      ["pertinence", "Pertinence", true],
      ["precision", "Précision", false],
      ["longueur", "Longueur", true],
      ["conclusion", "Conclusion", true],
      ["invention", "Aucune invention", true],
      ["regles", "Règles", true],
    ].map(([key, label, ok]) => ({ key, label, ok, reason: ok ? "Bien." : "Peu de chiffres." }));
    let release: (value: unknown) => void = () => undefined;
    POST.mockImplementation((path: string) =>
      path === "/api/letters/{draft_id}/review"
        ? new Promise((resolve) => {
            release = resolve;
          })
        : Promise.resolve({ data: letter(12, 2, { instruction: "plus court" }) }),
    );
    const wrapper = await mountView();
    await wrapper.find("[data-test=instruction]").setValue("plus court");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    // Pendant la relecture, le bouton le dit.
    expect(wrapper.find("[data-test=write]").text()).toContain("Relecture…");
    release({ data: letter(12, 2, { instruction: "plus court", review: { criteria, corrected: true } }) });
    await flushPromises();
    const line = wrapper.find("[data-test=review-line]");
    expect(line.attributes("aria-live")).toBe("polite");
    expect(line.text()).toBe("Relue : 6/7. À renforcer : précision.");
    const pills = wrapper.findAll("[data-test=review-detail] [data-test=state-pill]");
    expect(pills.map((p) => p.text())).toContain("À revoir");
    expect(pills.filter((p) => p.text() === "Réussi")).toHaveLength(6);
    expect(wrapper.find("[data-test=review-precision] .state-pill").classes()).toContain("todo");
    expect(wrapper.find("[data-test=review-detail] .state-pill.error").exists()).toBe(false);
  });

  it("consigne hors de portée : une ligne sous la consigne, gardée, pas de nouvelle version", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({
      data: undefined,
      error: { detail: "Je ne peux pas modifier tes coordonnées ici : va dans Profil." },
      response: { status: 422 },
    });
    const wrapper = await mountView();
    await wrapper.find("[data-test=instruction]").setValue("change mon téléphone");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    const note = wrapper.find("[data-test=instruction-note]");
    expect(note.attributes("aria-live")).toBe("polite");
    expect(note.text()).toBe("Je ne peux pas modifier tes coordonnées ici : va dans Profil.");
    expect(wrapper.find<HTMLTextAreaElement>("[data-test=instruction]").element.value).toBe("change mon téléphone");
    expect(wrapper.findAll("[data-test=version]")).toHaveLength(0);
  });

  it("erreur de l'API : message lisible", async () => {
    mockGet([]);
    POST.mockResolvedValue({ data: undefined, error: { detail: "plafond mensuel de l'IA atteint" } });
    const wrapper = await mountView();
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Plafond mensuel de l'IA atteint.");
  });

  it("coordonnées manquantes : renvoie vers les Réglages", async () => {
    const incomplete = letter(11, 1);
    incomplete.document.missing_identity = ["NPA", "localité"] as never[];
    mockGet([incomplete]);
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=missing-identity]").text()).toContain("NPA, localité");
  });
});

describe("barre de candidature", () => {
  it("postuler, télécharger, puis marquer comme envoyée sans quitter la page", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/offers/{offer_id}"
            ? offer
            : path === "/api/offers/{offer_id}/letters"
              ? [letter(11, 1)]
              : path === "/api/offers/{offer_id}/cvs"
                ? [{ id: 31, version: 1, created_at: "2026-10-05T08:00:00Z", edited_at: null }]
                : path === "/api/offers/{offer_id}/application-prefill"
                  ? {
                      offer_id: 7,
                      sent_at: "2026-10-05",
                      method: "electronique",
                      assigned_by_orp: false,
                      company: "Acme SA",
                      job_title: "Ingénieur DevOps junior",
                      application_url: "https://acme.example/jobs/1",
                    }
                  : [],
      }),
    );
    POST.mockResolvedValue({ data: { id: 5, company: "Acme SA", orp_month: "2026-10" } });
    const letterTab = await mountView();
    // Trois onglets numérotés (docs/47) : lettre et CV faits, cochés ; plus de barre du haut.
    expect(letterTab.find("[data-test=tab-letter] [data-test=step-done]").exists()).toBe(true);
    expect(letterTab.find("[data-test=tab-cv] [data-test=step-done]").exists()).toBe(true);
    // Une seule étape « courante » pour les lecteurs d'écran (WCAG 4.1.2, audit du 22.10.2026).
    expect(letterTab.findAll("[aria-current]").map((a) => a.attributes("data-test"))).toEqual(["tab-letter"]);
    expect(letterTab.find("[data-test=tab-letter]").attributes("aria-current")).toBe("step");
    expect(letterTab.find("[data-test=apply-bar]").exists()).toBe(false);
    expect(letterTab.find("[data-test=pdf]").text()).toBe("PDF");
    expect(letterTab.find("[data-test=save-letter]").exists()).toBe(false);
    letterTab.unmount();

    const wrapper = await mountView("/offres/7/preparer?doc=postuler");
    // Retour aux offres toujours possible.
    expect(wrapper.find("[data-test=back-to-offers]").attributes("href")).toBe("/candidatures/offres");
    const steps = wrapper.find("[data-test=apply-steps]");
    // Numérotées par compteur CSS (docs/51 n° 4).
    expect(steps.findAll(".apply-steps .apply-step h3").map((h) => h.text())).toEqual([
      "Postuler",
      "À recopier sur le site de l'employeur",
      "J'ai postulé",
    ]);
    expect(steps.find("[data-test=apply-contacts] h2").text()).toBe("Contacts chez Acme SA");
    expect(steps.find("[data-test=apply]").attributes("href")).toBe("https://acme.example/jobs/1");
    // Lettre et CV prêts : « Postuler » est le seul bouton plein (docs/29 §1.3).
    expect(steps.find("[data-test=apply]").classes()).toContain("primary-link");
    expect(wrapper.findAll(".primary, .primary-link")).toHaveLength(1);

    await steps.find("[data-test=mark-applied]").trigger("click");
    await flushPromises();
    expect(wrapper.find<HTMLInputElement>("[data-test=application-url]").element.value).toBe(
      "https://acme.example/jobs/1",
    );
    await wrapper.find("form.application-form").trigger("submit");
    await flushPromises();
    const [path, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications");
    expect(opts.body).toMatchObject({ offer_id: 7, application_url: "https://acme.example/jobs/1" });
    expect(document.querySelector("[data-test=sent-moment]")!.textContent).toContain("Candidature envoyée chez Acme SA");
    // Comptée pour l'ORP ; le retour aux offres est dans la barre du haut (offre envoyée).
    expect(document.querySelector("[data-test=sent-moment]")!.textContent).not.toContain("Retour aux offres");
  });
});

describe("Préparer sur téléphone (planche « Tri et panneau de commande »)", () => {
  it("le panneau : langue, consigne, « Versions · Télécharger » (feuille) et « Rédiger »", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px") || media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1), letter(12, 2, { instruction: "plus court" })]);
    POST.mockResolvedValue({ data: letter(13, 3, { language: "de" }) });
    const wrapper = await mountView();
    const bar = wrapper.find("[data-test=action-bar]");
    // La langue de la lettre est cochée tant qu'on n'en choisit pas d'autre.
    expect(bar.find("[data-test=language-fr]").attributes("aria-checked")).toBe("true");
    expect(bar.find("[data-test=instruction]").exists()).toBe(true);
    expect(bar.find("[data-test=write]").text()).toContain("Rédiger");
    // Les cartes de côté (rédiger, télécharger, versions) laissent place au panneau.
    expect(wrapper.find("[data-test=download-card]").exists()).toBe(false);
    await bar.find("[data-test=versions-open]").trigger("click");
    const sheet = wrapper.find("[data-test=versions-sheet]");
    expect(sheet.findAll("[data-test=sheet-version]")).toHaveLength(2);
    expect(sheet.find("[data-test=pdf]").text()).toContain("Lettre (PDF)");
    expect(sheet.find("[data-test=docx]").text()).toContain("Lettre (Word)");
    // Choisir une langue, puis rédiger : la nouvelle version part dans cette langue.
    await bar.find("[data-test=language-de]").trigger("click");
    await bar.find("[data-test=write]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toMatchObject({ language: "de" });
    vi.unstubAllGlobals();
  });
});
