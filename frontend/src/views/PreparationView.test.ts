import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useJobsMemory } from "../composables/useJobsMemory";
import { useUndo } from "../composables/useUndo";
import PreparationView from "./PreparationView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
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
    name: `Version ${version}`,
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

const FITS = { fits: true, overflow_lines: 0, adjusted: false, break_paragraph: null, break_word: null };
function mockGet(letters: unknown[], page: unknown = FITS): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/offers/{offer_id}"
          ? offer
          : path === "/api/offers/{offer_id}/letters"
            ? letters
            : path === "/api/letters/{draft_id}/page"
              ? page
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

    await wrapper.find("[data-test=letter-card] [data-test=language-fr]").trigger("click");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/letters", {
      params: { path: { offer_id: 7 } },
      body: { language: "fr", instruction: null, base_draft_id: null, modele: "moderne" },
    });
    const sheet = wrapper.find("[data-test=letter]");
    expect(sheet.text()).toContain("Renens, le 5 octobre 2026");
    expect(sheet.text()).toContain("Objet :");
    expect(sheet.text()).toContain("Blocs : Kubernetes");
    expect(wrapper.find<HTMLInputElement>("[data-test=subject]").element.value).toBe(
      "Candidature au poste d'ingénieur DevOps junior",
    );
    expect(wrapper.find("[data-test=docx]").attributes("href")).toBe("/api/letters/11/docx?modele=moderne");
    expect(wrapper.find("[data-test=pdf]").attributes("href")).toBe("/api/letters/11/pdf?modele=moderne");
  });

  it("la version modifiée en dernier est celle affichée ; les corrections s'enregistrent", async () => {
    mockGet([letter(12, 2), letter(11, 1, { edited_at: "2026-10-05T09:00:00Z" })]);
    PUT.mockResolvedValue({ data: letter(11, 1, { subject: "Candidature", edited_at: "2026-10-05T10:00:00Z" }) });
    const wrapper = await mountView();
    // Les versions sont dans le panneau « Versions et téléchargement » (§2.2), ouvert par la ligne « Versions · 2 ».
    expect(wrapper.get("[data-test=versions-open]").text()).toContain("Versions · 2");
    expect(wrapper.findAll("[data-test=sheet-version]")).toHaveLength(2);
    // La version affichée est marquée (pastille de sélection, aria-current).
    expect(wrapper.find(".versions [aria-current=page]").text()).toContain("Version 1");

    await wrapper.find("[data-test=subject]").setValue("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(false);
    await wrapper.find("[data-test=save-letter]").trigger("click");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { params: unknown; body: { subject: string } }];
    expect(path).toBe("/api/letters/{draft_id}");
    expect(opts.body.subject).toBe("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(true);
  });

  it("une consigne longue : un nom court, la consigne entière en sous-titre et au-dessus de la lettre, sans « … »", async () => {
    const long = "Insiste davantage sur Kubernetes et Terraform, raccourcis ".repeat(6).trim();
    expect(long.length).toBeGreaterThan(300);
    mockGet([letter(12, 2, { instruction: long }), letter(11, 1)]);
    const wrapper = await mountView();
    const versions = wrapper.findAll("[data-test=sheet-version]");
    const named = versions.find((v) => v.text().includes("Insiste"))!;
    expect(named.find(".grouped-row-title").text()).toBe("Version 2");
    expect(named.find(".grouped-row-description").text()).toBe(long);
    expect(named.text()).not.toContain("…");
    // Sans consigne : le nom, puis la version, la langue et la date en sous-titre.
    const first = versions.find((v) => v.find(".grouped-row-title").text() === "Version 1")!;
    expect(first.find(".grouped-row-description").text()).toContain("v1 · Français");
    // Sur ordinateur, « Consigne : … » ne s'affiche plus au-dessus de la lettre (lot 15.1).
    await named.trigger("click");
    expect(wrapper.find("[data-test=version-instruction]").exists()).toBe(false);
    // La consigne passe par la zone de saisie commune sous la lettre (maquette du 8 novembre).
    expect(wrapper.find("[data-test=prep-revise] [data-test=composer-input]").attributes("placeholder")).toBe("Demander une modification de la lettre");
  });

  it("nouvelle version avec consigne : part de la version affichée", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({ data: letter(12, 2, { instruction: "plus court", name: "Plus courte" }) });
    const wrapper = await mountView();
    await wrapper.find("[data-test=prep-revise] [data-test=composer-input]").setValue("plus court");
    await wrapper.find("[data-test=prep-revise] [data-test=composer-send]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toEqual({ language: null, instruction: "plus court", base_draft_id: 11, modele: "moderne" });
    expect(wrapper.find(".versions [aria-current=page] .grouped-row-title").text()).toBe("Plus courte");
  });

  it("les retouches proposées : « Plus court » part en consigne ; plus de puce « En allemand » (9 novembre, §2.2 et §9)", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({ data: letter(12, 2, { instruction: "Plus court" }) });
    const wrapper = await mountView();
    const chips = () => wrapper.findAll("[data-test=prep-revise] .suggestion-chips button");
    await chips().find((b) => b.text() === "Plus court")!.trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toMatchObject({ instruction: "Plus court", base_draft_id: 11 });
    expect(chips().map((b) => b.text())).not.toContain("En allemand");
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
    await wrapper.find("[data-test=prep-revise] [data-test=composer-input]").setValue("plus court");
    await wrapper.find("[data-test=prep-revise] [data-test=composer-send]").trigger("click");
    await flushPromises();
    // Pendant la relecture, le bouton le dit.
    expect(wrapper.find("[data-test=write]").text()).toContain("Relecture…");
    release({ data: letter(12, 2, { instruction: "plus court", review: { criteria, corrected: true } }) });
    await flushPromises();
    const line = wrapper.find("[data-test=review-line]");
    expect(line.attributes("aria-live")).toBe("polite");
    expect(line.text()).toBe("Relue : 6/7. À renforcer : précision.");
    // Sur ordinateur (§2.2) : la ligne Relecture de « Ta candidature » ouvre le panneau, le point à renforcer d'abord.
    const row = wrapper.get("[data-test=review-open]");
    expect(row.text()).toContain("6 sur 7, 1 point à renforcer");
    expect(row.find(".prep-file-sub").classes()).toContain("todo");
    await row.trigger("click");
    const sheet = wrapper.get("[data-test=review-sheet]");
    expect(sheet.findAll("h3").map((h) => h.text())).toEqual(["À renforcer · 1", "Vérifié · 6"]);
    expect(sheet.get("[data-test=review-precision]").text()).toContain("Peu de chiffres.");
    expect(sheet.text()).toContain("corrigée une fois");
  });

  it("consigne hors de portée : une ligne sous la consigne, gardée, pas de nouvelle version", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({
      data: undefined,
      error: { detail: "Je ne peux pas modifier tes coordonnées ici : va dans Profil." },
      response: { status: 422 },
    });
    const wrapper = await mountView();
    await wrapper.find("[data-test=prep-revise] [data-test=composer-input]").setValue("change mon téléphone");
    await wrapper.find("[data-test=prep-revise] [data-test=composer-send]").trigger("click");
    await flushPromises();
    const note = wrapper.find("[data-test=instruction-note]");
    expect(note.attributes("aria-live")).toBe("polite");
    expect(note.text()).toBe("Je ne peux pas modifier tes coordonnées ici : va dans Profil.");
    expect(wrapper.find<HTMLTextAreaElement>("[data-test=prep-revise] [data-test=composer-input]").element.value).toBe("change mon téléphone");
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
              ? [letter(11, 1, { read_at: "2026-10-05T09:00:00Z" })]
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
    const current = letterTab.findAll("[aria-current]").filter((a) => !a.element.closest("dialog"));
    expect(current.map((a) => a.attributes("data-test"))).toEqual(["tab-letter"]);
    expect(letterTab.find("[data-test=tab-letter]").attributes("aria-current")).toBe("step");
    expect(letterTab.find("[data-test=apply-bar]").exists()).toBe(false);
    expect(letterTab.find("[data-test=pdf]").text()).toBe("Lettre (PDF)");
    expect(letterTab.find("[data-test=save-letter]").exists()).toBe(false);
    letterTab.unmount();

    const wrapper = await mountView("/offres/7/preparer?doc=postuler");
    // Le retour à l'offre, toujours possible (C1) ; sur ordinateur, le poste en titre (lot 15.1), « Ma candidature »
    // seulement dans le titre de l'onglet.
    expect(wrapper.find("[data-test=back-to-offer]").attributes("href")).toBe("/candidatures/offres/7");
    expect(wrapper.find("h1").text()).toBe(offer.title);
    expect(wrapper.find("[data-test=prep-offer-title]").text()).toBe(offer.title);
    expect(document.title).toBe(`Ma candidature, ${offer.title}, jobA1`);
    // La ligne de l'entreprise, sans le canton (maquette : « Alpstack · Lausanne »).
    expect(wrapper.find(".prep-desk-title p").text()).toMatch(/· Lausanne$/);
    const steps = wrapper.find("[data-test=apply-steps]");
    // Postuler (C7) : où l'annonce se postule, les pièces, ce qu'on recopie, puis un contact dans la fiche.
    expect(steps.findAll("h2").map((h) => h.text())).toEqual([
      "L'annonce se postule chez l'employeur",
      "À recopier sur le formulaire",
    ]);
    expect(steps.find("[data-test=sheet-letter]").text()).toBe("Lettre.pdf");
    expect(steps.find("[data-test=sheet-cv]").attributes("href")).toBe("/api/cvs/31/pdf?modele=moderne");
    // Sur ordinateur, pas de ligne « Modèle … » (maquette téléphone seulement).
    expect(steps.find("[data-test=apply-template-note]").exists()).toBe(false);
    expect(steps.find("[data-test=find-contact]").text()).toBe("Trouver un contact chez Acme SA");
    expect(steps.find("[data-test=find-contact]").attributes("href")).toBe("/candidatures/offres/7#contacts");
    // D'abord le formulaire, seul bouton plein (docs/29 §1.3) ; une fois ouvert, « J'ai postulé » (C8).
    const apply = steps.find("[data-test=apply]");
    expect(apply.attributes("href")).toBe("https://acme.example/jobs/1");
    expect(apply.classes()).toContain("primary-link");
    expect(wrapper.findAll(".primary, .primary-link")).toHaveLength(1);
    expect(steps.find("[data-test=mark-applied]").exists()).toBe(false);
    // Déjà postulé ailleurs (e-mail, téléphone, page rechargée) : un lien tertiaire, pas un second bouton plein.
    expect(steps.find("[data-test=already-applied]").text()).toContain("J'ai déjà postulé");
    expect(steps.find("[data-test=already-applied]").classes()).toContain("link");
    apply.element.addEventListener("click", (event) => event.preventDefault());
    await apply.trigger("click");
    expect(steps.find("[data-test=apply]").text()).toBe("Rouvrir le site de l'employeur (nouvel onglet)");
    expect(steps.find("[data-test=already-applied]").exists()).toBe(false);
    expect(wrapper.findAll(".primary, .primary-link")).toHaveLength(1);

    // « J'ai postulé » enregistre tout de suite, avec les valeurs de l'annonce et la date du jour.
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/offers/{offer_id}/application-prefill"
            ? { offer_id: 7, sent_at: "2026-10-05", method: "electronique", company: "Acme SA", job_title: "Ingénieur DevOps junior", application_url: "https://acme.example/jobs/1" }
            : path === "/api/orp"
              ? { count: 9, target: 10 }
              : null,
      }),
    );
    POST.mockResolvedValue({ data: { id: 5, company: "Acme SA", job_title: "Ingénieur DevOps junior", sent_at: "2026-10-05", orp_month: "2026-10" } });
    await steps.find("[data-test=mark-applied]").trigger("click");
    await flushPromises();
    const [path, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications");
    expect(opts.body).toMatchObject({ offer_id: 7, sent_at: "2026-10-05", application_url: "https://acme.example/jobs/1" });

    // « Candidature envoyée. » (maquette CandidatureEnvoyee, docs/141, 8) à la place de la page : le personnage à
    // l'avion, ce qui compte pour l'ORP, « Voir mes candidatures », « Préparer la prochaine », « Je n'ai pas postulé ».
    const done = wrapper.find("[data-test=sent-moment]");
    expect(done.find("h1").text()).toBe("Candidature envoyée.");
    expect(done.find("[role=status]").exists()).toBe(true);
    expect(done.find("[data-illustration=personnage]").attributes("data-pose")).toBe("avion");
    expect(done.find("[data-mood-animation]").exists()).toBe(false);
    expect(done.text()).toContain("Ingénieur DevOps junior chez Acme SA. Elle compte pour l’ORP : 9 recherches sur 10 ce mois.");
    expect(done.find("[data-test=sent-follow-up]").exists()).toBe(false);
    expect(done.find("[data-test=sent-applications]").attributes("href")).toBe("/candidatures/suivi");
    expect(done.find("[data-test=next-offer]").attributes("href")).toBe("/candidatures/offres");
    expect(wrapper.find("[data-test=apply-steps]").exists()).toBe(false);

    // « Je n'ai pas postulé » : l'offre revient en préparation (le menu y ramène) ; la candidature part après 6 s.
    expect(done.find("[data-test=cancel-applied]").text()).toBe("Je n'ai pas postulé");
    useJobsMemory().remember("/candidatures/offres/7/preparer?doc=postuler");
    useJobsMemory().sent(7);
    expect(useJobsMemory().last.value).toBe("/candidatures/suivi");
    DELETE.mockResolvedValue({ response: { ok: true } });
    await done.find("[data-test=cancel-applied]").trigger("click");
    expect(useJobsMemory().last.value).toBe("/candidatures/offres/7/preparer?doc=postuler");
    expect(wrapper.find("[data-test=sent-moment]").exists()).toBe(false);
    expect(wrapper.find("[data-test=mark-applied]").exists()).toBe(false);
    expect(wrapper.find("[data-test=apply]").classes()).toContain("primary-link");
    await useUndo().undo();
    await flushPromises();
    expect(wrapper.find("[data-test=sent-moment]").exists()).toBe(true);
    await wrapper.find("[data-test=cancel-applied]").trigger("click");
    await useUndo().flush();
    expect(DELETE).toHaveBeenCalledWith("/api/applications/{application_id}", expect.objectContaining({ params: { path: { application_id: 5 } } }));
  });

  it("« C'est fait ! » remplace « Candidature notée » quand l'envoi atteint l'objectif, une fois par mois (B10)", async () => {
    localStorage.clear();
    const orp = { month: "2026-10", count: 10, target: 10, rows: [], holder: { name: "Kevin", address: null }, searches: [], changed_after_submit: false };
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/offers/{offer_id}"
            ? offer
            : path === "/api/offers/{offer_id}/application-prefill"
              ? { offer_id: 7, sent_at: "2026-10-05", method: "electronique", company: "Acme SA", job_title: "Ingénieur DevOps junior" }
              : path === "/api/orp"
                ? orp
                : [],
      }),
    );
    POST.mockResolvedValue({ data: { id: 5, company: "Acme SA", job_title: "Ingénieur DevOps junior", sent_at: "2026-10-05", orp_month: "2026-10" } });
    const wrapper = await mountView("/offres/7/preparer?doc=postuler");
    await wrapper.find("[data-test=already-applied]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=sent-moment]").exists()).toBe(false);
    expect(wrapper.find("[data-test=goal-reached] h1").text()).toBe("C'est fait !");
    // Retenu sur l'appareil, avec la même clé que la carte de l'Accueil.
    expect(localStorage.getItem("jobA1.orp-goal.2026-10")).toBe("1");

    // « Je n'ai pas postulé » : l'objectif n'est plus atteint, la fête pourra revenir.
    DELETE.mockResolvedValue({ response: { ok: true } });
    await wrapper.find("[data-test=cancel-applied]").trigger("click");
    expect(wrapper.find("[data-test=goal-reached]").exists()).toBe(false);
    expect(localStorage.getItem("jobA1.orp-goal.2026-10")).toBeNull();
    await useUndo().undo();
    await flushPromises();
    expect(wrapper.find("[data-test=goal-reached]").exists()).toBe(true);

    // Déjà vue ce mois-ci : « Candidature notée », comme d'habitude.
    const again = await mountView("/offres/7/preparer?doc=postuler");
    await again.find("[data-test=already-applied]").trigger("click");
    await flushPromises();
    expect(again.find("[data-test=goal-reached]").exists()).toBe(false);
    expect(again.find("[data-test=sent-moment] h1").text()).toBe("Candidature envoyée.");
    localStorage.clear();
  });

  it("« J'ai déjà postulé » enregistre l'envoi sans rouvrir le formulaire", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/offers/{offer_id}"
            ? offer
            : path === "/api/offers/{offer_id}/application-prefill"
              ? { offer_id: 7, sent_at: "2026-10-05", method: "electronique", company: "Acme SA", job_title: "Ingénieur DevOps junior" }
              : path === "/api/orp"
                ? { count: 3, target: null }
                : [],
      }),
    );
    POST.mockResolvedValue({ data: { id: 5, company: "Acme SA", job_title: "Ingénieur DevOps junior", sent_at: "2026-10-05", orp_month: "2026-10" } });
    const wrapper = await mountView("/offres/7/preparer?doc=postuler");
    await wrapper.find("[data-test=already-applied]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/applications", { body: expect.objectContaining({ offer_id: 7, sent_at: "2026-10-05" }) });
    expect(wrapper.find("[data-test=sent-moment] h1").text()).toBe("Candidature envoyée.");
    expect(wrapper.find("[data-test=sent-orp]").text()).toBe("3 recherches");
  });

  it("une candidature déjà envoyée : « Envoyée le … » et le lien vers le suivi, plus d'étape « Suivre » (Q1)", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/offers/{offer_id}"
            ? { ...offer, status: "applied" }
            : path === "/api/applications"
              ? [{ id: 5, sent_at: "2026-10-05" }]
              : [],
      }),
    );
    const wrapper = await mountView("/offres/7/preparer?doc=suivre");
    expect(wrapper.find("[data-test=applied-notice]").text()).toBe("Envoyée le 5 octobre. Voir le suivi");
    expect(wrapper.find("[data-test=tab-follow]").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-apply]").attributes("aria-current")).toBe("step");
    expect(wrapper.find("[data-test=tab-apply] [data-test=step-done]").exists()).toBe(true);
    expect(wrapper.find("[data-test=mark-applied]").exists()).toBe(false);
  });
});

describe("Ma candidature sur téléphone (maquette Preparer, étape 7a)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("un seul bouton plein en bas ; la langue choisie dans la feuille le change en « Rédiger à nouveau en allemand » (C3, §9)", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px") || media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1), letter(12, 2, { instruction: "plus court", read_at: "2026-10-05T09:00:00Z" })]);
    POST.mockResolvedValue({ data: letter(13, 3, { language: "de" }) });
    const wrapper = await mountView();
    const bar = wrapper.find("[data-test=action-bar]");
    // Rien à rédiger : un seul bouton, « J'ai relu, continuer ».
    expect(bar.find("[data-test=next-step]").text()).toBe("J’ai relu, continuer");
    expect(bar.find("[data-test=write]").exists()).toBe(false);
    expect(wrapper.findAll(".primary, .primary-link")).toHaveLength(1);
    // En-tête : plus d'anneau de note (§9).
    expect(wrapper.find("[data-test=prep-offer] .score-ring").exists()).toBe(false);
    // La carte de la lettre : le titre, « Moderne · Français » dessous et « Changer » ; plus de FR / DE / EN à l'écran.
    const card = wrapper.find("[data-test=letter-card]");
    expect(card.find("h2").text()).toBe("Lettre de motivation");
    expect(card.get("[data-test=layout-summary]").text()).toBe("Moderne · Français");
    expect(card.find(".doc-language").exists()).toBe(false);
    expect(wrapper.find("[data-test=template-row]").exists()).toBe(false);
    const change = card.get("[data-test=layout-change]");
    expect(change.text()).toBe("Changer");
    expect(change.attributes("aria-haspopup")).toBe("dialog");
    expect(card.find("[data-test=edit-text]").exists()).toBe(false);
    // Les cartes de côté laissent place au « ⋯ » de la tête (versions et téléchargement).
    expect(wrapper.find("[data-test=download-card]").exists()).toBe(false);
    await wrapper.find("[data-test=versions-open]").trigger("click");
    const versions = wrapper.find("[data-test=versions-sheet]");
    expect(versions.findAll("[data-test=sheet-version]")).toHaveLength(2);
    expect(versions.find("[data-test=pdf]").text()).toContain("Lettre (PDF)");
    // La feuille : la langue en trois boutons en toutes lettres. Choisir ne rédige rien ; le bouton plein le propose.
    await change.trigger("click");
    const sheet = wrapper.get("[data-test=layout-sheet]");
    const pills = sheet.findAll("[data-test^=language-][role=radio]");
    expect(pills.map((b) => b.text())).toEqual(["Français", "Deutsch", "English"]);
    expect(sheet.get("[data-test=language-fr]").attributes("aria-checked")).toBe("true");
    await sheet.get("[data-test=language-de]").trigger("click");
    expect(POST).not.toHaveBeenCalled();
    expect(card.get("[data-test=layout-summary]").text()).toBe("Moderne · Deutsch");
    expect(bar.find("[data-test=write]").text()).toContain("Rédiger à nouveau en allemand");
    await bar.find("[data-test=write]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toMatchObject({ language: "de" });
  });

  it("les puces de retouche n'apparaissent qu'avec le focus dans la zone de saisie ; l'aperçu passe de 384 à 300 px (§9)", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1)]);
    const wrapper = await mountView();
    const revise = wrapper.get("[data-test=prep-revise]");
    const preview = () => wrapper.get("[data-test=letter-card] [data-test=doc-preview]");
    expect(revise.text()).not.toContain("Retoucher la lettre");
    expect(revise.find(".suggestion-chips").exists()).toBe(false);
    expect(preview().classes()).toContain("doc-preview-tall");
    expect(preview().classes()).not.toContain("doc-preview-composing");
    await revise.get("[data-test=composer-input]").trigger("focusin");
    expect(revise.findAll(".suggestion-chips button").map((b) => b.text())).toEqual(["Plus court", "Plus formel"]);
    expect(preview().classes()).toContain("doc-preview-composing");
    await revise.get("[data-test=composer-input]").trigger("focusout", { relatedTarget: null });
    expect(revise.find(".suggestion-chips").exists()).toBe(false);
  });

  it("« J'ai relu, continuer » : plus de case ; le bouton note la relecture et passe au CV (§9, C11)", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1)]);
    PUT.mockResolvedValue({ data: letter(11, 1, { read_at: "2026-10-05T09:00:00Z" }) });
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=letter-read]").exists()).toBe(false);
    expect(wrapper.find("[data-test=next-step-hint]").exists()).toBe(false);
    expect(wrapper.find("[data-test=tab-letter] [data-test=step-done]").exists()).toBe(false);
    // L'étape CV reste ouverte.
    expect(wrapper.find("[data-test=tab-cv]").attributes("href")).toContain("doc=cv");
    await wrapper.get("[data-test=action-bar] [data-test=next-step]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/letters/{draft_id}/read", { params: { path: { draft_id: 11 } }, body: { read: true } });
    expect(wrapper.vm.$router.currentRoute.value.query.doc).toBe("cv");
    expect(wrapper.find("[data-test=tab-letter] [data-test=step-done]").exists()).toBe(true);
  });

  it("ordinateur (§2.2) : vignettes de modèle, carte « Ta candidature », « J’ai relu, continuer » dans la colonne de droite", async () => {
    mockGet([letter(11, 1)]);
    PUT.mockResolvedValue({ data: letter(11, 1, { read_at: "2026-10-05T09:00:00Z" }) });
    const wrapper = await mountView();
    const steps = wrapper.find("[data-test=prep-desk-head] .step-tabs");
    expect(steps.text()).toContain("1. Lettre");
    expect(steps.text()).toContain("2. CV");
    // Quatre vignettes de 48 × 64, une seule choisie.
    const thumbs = wrapper.findAll("[data-test=layout-card] .layout-card-thumbs button");
    expect(thumbs.map((b) => b.text())).toEqual(["Sobre", "Moderne", "Bandeau", "Classique"]);
    expect(thumbs.every((b) => b.find("svg[width='48'][height='64']").exists())).toBe(true);
    expect(thumbs.filter((b) => b.attributes("aria-pressed") === "true")).toHaveLength(1);
    // « Ta candidature » : Versions et CV adapté ; la retouche reste à gauche, sans le bouton.
    const file = wrapper.get("[data-test=prep-file]");
    expect(file.find("h2").text()).toBe("Ta candidature");
    expect(file.get("[data-test=versions-open]").text()).toContain("Versions · 1");
    expect(file.get("[data-test=cv-row]").text()).toContain("CV adapté");
    expect(wrapper.find("[data-test=prep-desk-bottom] [data-test=letter-read]").exists()).toBe(false);
    expect(wrapper.find("[data-test=prep-desk-bottom] [data-test=composer-input]").exists()).toBe(true);
    const read = wrapper.get("[data-test=prep-aside] [data-test=letter-read]");
    expect(read.text()).toBe("J’ai relu, continuer");
    await read.trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/letters/{draft_id}/read", { params: { path: { draft_id: 11 } }, body: { read: true } });
    expect(wrapper.vm.$router.currentRoute.value.query.doc).toBe("cv");
  });

  it("ordinateur (§2.2) : la note dit « Proche de ton profil » et ouvre le panneau Compatibilité", async () => {
    const scored = { ...offer, score: 80, strengths: [{ text: "Kubernetes : 40 services" }], gaps: [{ text: "Allemand : B2 demandé" }] };
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/offers/{offer_id}" ? scored : path === "/api/offers/{offer_id}/letters" ? [letter(11, 1)] : path === "/api/letters/{draft_id}/page" ? FITS : [] }),
    );
    const wrapper = await mountView();
    const score = wrapper.get("[data-test=prep-score]");
    expect(score.text()).toContain("Proche de ton profil");
    expect(score.text()).toContain("Voir la compatibilité");
    expect(score.attributes("aria-haspopup")).toBe("dialog");
    await score.trigger("click");
    const sheet = wrapper.get("[data-test=compat-sheet]");
    expect(sheet.text()).toContain("Kubernetes");
    expect(sheet.text()).toContain("B2 demandé");
  });

  it("ordinateur (§2.2) : sans lettre, la page A4 grisée et la carte « Pas encore de lettre » avec « Générer la lettre »", async () => {
    mockGet([]);
    const wrapper = await mountView();
    const empty = wrapper.get("[data-test=no-letter]");
    expect(empty.text()).toContain("Pas encore de lettre pour cette offre");
    expect(empty.get("[data-test=write]").text()).toContain("Générer la lettre");
    expect(wrapper.find("[data-test=prep-file]").exists()).toBe(false);
  });

  it("« J'ai relu, continuer » refusé (démo) : le refus s'affiche et l'on reste sur la lettre", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1)]);
    PUT.mockResolvedValue({ error: { detail: "Dans la démo, rien n'est enregistré." } });
    const wrapper = await mountView();
    await wrapper.get("[data-test=action-bar] [data-test=next-step]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[role=alert]").text()).toBe("Dans la démo, rien n'est enregistré.");
    expect(wrapper.vm.$router.currentRoute.value.query.doc).toBeUndefined();
  });

  it("le modèle (Kevin, 2026-11-05 ; feuille « Mise en page et langue », §9) : l'aperçu de la lettre et le PDF dans le modèle choisi", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1)]);
    const wrapper = await mountView();
    // « Changer » ouvre la feuille ; plus de vignettes ni de carte « Mise en page » sur l'écran.
    await wrapper.get("[data-test=layout-change]").trigger("click");
    const sheet = wrapper.get("[data-test=layout-sheet]");
    const picker = sheet.find("[data-test=template-picker]");
    expect(sheet.text()).toContain("Mise en page et langue");
    expect(sheet.text()).toContain("Le même modèle s’applique à ta lettre et à ton CV.");
    expect(sheet.text()).toContain("Tient sur une page A4.");
    expect(sheet.text()).toContain("Langue de la lettre");
    expect(picker.classes()).toContain("tpl-picker-grid");
    expect(picker.findAll("[role=radio] .tpl-card-label").map((r) => r.text())).toEqual(["Sobre", "Moderne", "Bandeau", "Classique"]);
    // La vignette Classique porte les initiales de l'expéditeur, comme la maquette (« K D »).
    expect(picker.find("[data-test=template-classique] .tpl-thumb-initials").text()).toMatch(/^\p{Lu} \p{Lu}$/u);
    const preview = () => wrapper.find("[data-test=letter-card] [data-test=doc-preview]");
    expect(preview().attributes("data-template")).toBe("moderne");
    await picker.find("[data-test=template-bandeau]").trigger("click");
    expect(picker.find("[data-test=template-bandeau]").attributes("aria-checked")).toBe("true");
    expect(preview().attributes("data-template")).toBe("bandeau");
    expect(wrapper.get("[data-test=layout-summary]").text()).toBe("Bandeau · Français");
    expect(wrapper.find("[data-test=edit-text]").exists()).toBe(false);
    await wrapper.find("[data-test=versions-open]").trigger("click");
    expect(wrapper.find("[data-test=versions-sheet] [data-test=pdf]").attributes("href")).toBe("/api/letters/11/pdf?modele=bandeau");
    await picker.find("[data-test=template-moderne]").trigger("click");
  });

  it("Postuler, sur téléphone : « Modèle Moderne, en allemand. » sous Lettre.pdf, le vrai modèle et la vraie langue", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1, { language: "de" })]);
    const wrapper = await mountView("/offres/7/preparer?doc=postuler");
    const note = wrapper.find("[data-test=apply-where] [data-test=apply-template-note]");
    expect(note.text()).toBe("Modèle Moderne, en allemand.");
  });

  it("sans lettre : l'aperçu vide du modèle à la place de « Aucune lettre »", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([]);
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=letter-card] [data-test=doc-preview-empty]").exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Aucune lettre pour cette offre.");
  });

  it("sans lettre : « Rédiger la lettre », ou « Rédiger en anglais » une fois la langue choisie", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([]);
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=action-bar] [data-test=write]").text()).toContain("Rédiger la lettre");
    await wrapper.find("[data-test=letter-card] [data-test=language-en]").trigger("click");
    expect(wrapper.find("[data-test=action-bar] [data-test=write]").text()).toContain("Rédiger en anglais");
  });
});

describe("« Pas vrai » (30.10.2026)", () => {
  afterEach(() => vi.unstubAllGlobals());
  function choose(wrapper: Awaited<ReturnType<typeof mountView>>, index: number, from: number, to: number) {
    const area = wrapper.findAll("[data-test=paragraph]")[index]!;
    const el = area.element as HTMLTextAreaElement;
    el.setSelectionRange(from, to);
    return area.trigger("select");
  }

  it("ordinateur : la sélection s'étend à la phrase, « Pas vrai », retirer, « Annuler » pendant 6 s", async () => {
    const two = letter(11, 1, {
      paragraphs: [
        { text: "Votre annonce a retenu mon attention.", chunk_ids: [] },
        { text: "J'administre un cluster K3s. Il tourne en production à l'État de Vaud.", chunk_ids: [1] },
      ],
    });
    mockGet([two]);
    POST.mockResolvedValue({ data: { letter: { ...two, paragraphs: [two.paragraphs[0], { text: "J'administre un cluster K3s.", chunk_ids: [1] }] }, claim_id: 5 } });
    const wrapper = await mountView();
    const text = two.paragraphs[1]!.text;
    await choose(wrapper, 1, text.indexOf("production"), text.indexOf("production") + 5);
    await wrapper.find("[data-test=false-claim]").trigger("click");
    const sheet = wrapper.find("[data-test=false-claim-sheet]");
    expect(sheet.find("[data-test=false-claim-quote]").text()).toBe("« Il tourne en production à l'État de Vaud. »");
    await sheet.find("[data-test=false-claim-confirm]").trigger("click");
    await flushPromises();
    // Retirée tout de suite à l'écran ; la demande part après 6 s, sauf « Annuler ».
    const area = () => wrapper.findAll("[data-test=paragraph]")[1]!.element as HTMLTextAreaElement;
    expect(area().value).toBe("J'administre un cluster K3s.");
    expect(POST).not.toHaveBeenCalled();
    await useUndo().undo();
    await flushPromises();
    expect(area().value).toBe(text);
    await choose(wrapper, 1, text.indexOf("production"), text.indexOf("production") + 5);
    await wrapper.find("[data-test=false-claim]").trigger("click");
    await wrapper.find("[data-test=false-claim-confirm]").trigger("click");
    await useUndo().flush();
    await flushPromises();
    expect(POST).toHaveBeenCalledWith(
      "/api/letters/{draft_id}/false-claim",
      expect.objectContaining({ body: { sentence: "Il tourne en production à l'État de Vaud.", mode: "remove" } }),
    );
  });

  it("une phrase qui est tout le paragraphe : le paragraphe disparaît, « Annuler » le remet", async () => {
    mockGet([letter(11, 1)]);
    const wrapper = await mountView();
    await choose(wrapper, 1, 0, 5);
    await wrapper.find("[data-test=false-claim]").trigger("click");
    await wrapper.find("[data-test=false-claim-confirm]").trigger("click");
    await flushPromises();
    // Aucun paragraphe vide ne reste à sa place.
    expect(wrapper.findAll("[data-test=paragraph]")).toHaveLength(1);
    expect(wrapper.findAll(".letter-paragraph")).toHaveLength(1);
    await useUndo().undo();
    await flushPromises();
    const texts = wrapper.findAll("[data-test=paragraph]").map((p) => (p.element as HTMLTextAreaElement).value);
    expect(texts).toEqual(["Votre annonce a retenu mon attention.", "J'administre un cluster K3s."]);
  });

  it("réécrire d'après le profil : une nouvelle version relue ; « Annuler » revient à l'ancienne", async () => {
    const first = letter(11, 1);
    mockGet([first]);
    const rewritten = letter(12, 2, { instruction: "Pas vrai : « J'administre un cluster K3s. »" });
    POST.mockImplementation((path: string) =>
      Promise.resolve({ data: path.endsWith("/review") ? rewritten : { letter: rewritten, claim_id: 7 } }),
    );
    DELETE.mockResolvedValue({ response: { ok: true } });
    const wrapper = await mountView();
    await choose(wrapper, 1, 0, 5);
    await wrapper.find("[data-test=false-claim]").trigger("click");
    await wrapper.find("[data-test=false-claim-rewrite] input").setValue(true);
    await wrapper.find("[data-test=false-claim-confirm]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith(
      "/api/letters/{draft_id}/false-claim",
      expect.objectContaining({ body: { sentence: "J'administre un cluster K3s.", mode: "rewrite" } }),
    );
    expect(POST).toHaveBeenCalledWith("/api/letters/{draft_id}/review", expect.anything());
    expect(wrapper.find(".versions [aria-current=page] .grouped-row-description").text()).toContain("Pas vrai");
    await useUndo().undo();
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/forbidden-claims/{claim_id}", { params: { path: { claim_id: 7 } } });
    expect(wrapper.find(".versions [aria-current=page] .grouped-row-description").text()).not.toContain("Pas vrai");
  });

  it("téléphone : toucher une phrase la choisit, « Pas vrai » remplace « Rédiger » dans le panneau", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px") || media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet([letter(11, 1)]);
    const wrapper = await mountView();
    // Sur téléphone, la lettre est d'abord un aperçu dans le modèle ; touché, il ouvre la lettre entière.
    expect(wrapper.find("[data-test=paragraph]").exists()).toBe(false);
    await wrapper.find("[data-test=doc-preview]").trigger("click");
    const area = wrapper.findAll("[data-test=paragraph]")[1]!;
    (area.element as HTMLTextAreaElement).setSelectionRange(3, 3);
    await area.trigger("click");
    const bar = wrapper.find("[data-test=action-bar]");
    expect(bar.find("[data-test=false-claim-chosen]").text()).toBe("« J'administre un cluster K3s. »");
    expect(bar.find("[data-test=next-step]").exists()).toBe(false);
    // Une tâche à la fois : ni la langue ni la consigne pendant le choix.
    expect(wrapper.find("[data-test=prep-revise]").exists()).toBe(false);
    await bar.find("[data-test=false-claim-cancel]").trigger("click");
    expect(wrapper.find("[data-test=action-bar] [data-test=next-step]").exists()).toBe(true);
    expect(wrapper.find("[data-test=prep-revise]").exists()).toBe(true);
  });
  it("une page A4 : « Tient sur une page A4 », ou le débordement, la marque de fin de page et « Raccourcir »", async () => {
    mockGet([letter(11, 1)]);
    let wrapper = await mountView();
    expect(GET).toHaveBeenCalledWith("/api/letters/{draft_id}/page", { params: { path: { draft_id: 11 }, query: { modele: "moderne" } } });
    // Sur ordinateur, la ligne de la page est dans « Mise en page » (lot 15.1).
    expect(wrapper.find("[data-test=layout-note]").text()).toMatch(/^Tient sur une page A4 · \d+ mots$/);
    expect(wrapper.find("[data-test=page-end]").exists()).toBe(false);
    wrapper.unmount();

    mockGet([letter(11, 1)], { fits: false, overflow_lines: 3, adjusted: true, break_paragraph: 1, break_word: 3 });
    POST.mockResolvedValue({ data: letter(12, 2, { instruction: "Raccourcir pour tenir sur une page A4", name: "Plus courte" }) });
    wrapper = await mountView();
    expect(wrapper.find("[data-test=layout-note]").text()).toContain("Déborde de 3 lignes ·");
    // La page 1 se termine dans le 2e paragraphe, après « J'administre un cluster ».
    const marks = wrapper.findAll("[data-test=page-end]");
    expect(marks).toHaveLength(1);
    expect(marks[0]!.text()).toBe("Fin de la page A4 dans ce paragraphe, après «\u00a0J'administre un cluster\u00a0».");
    expect(wrapper.findAll(".letter-paragraph")[1]!.find("[data-test=page-end]").exists()).toBe(true);

    await wrapper.find("[data-test=shorten]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toEqual({ language: null, instruction: "Raccourcir pour tenir sur une page A4", base_draft_id: 11, modele: "moderne" });
  });
});
