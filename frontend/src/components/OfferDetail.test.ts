import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OfferDetail from "./OfferDetail.vue";

const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: vi.fn(() => Promise.resolve({ data: undefined })), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

function offer(extra: Record<string, unknown> = {}) {
  return {
    id: 4,
    title: "Ingénieur DevOps",
    company: "Exemple SA",
    location: "Lausanne",
    status: "to_review",
    first_seen_at: "2026-10-05T08:00:00Z",
    last_seen_at: "2026-10-05T08:00:00Z",
    seen_count: 1,
    links: [{ source: "indeed", url: "https://ch.indeed.com/viewjob?jk=1" }],
    apply_url: null,
    apply_kind: null,
    employer_url: null,
    employer_url_source: null,
    employer_status: null,
    employer_checked_at: null,
    ...extra,
  };
}

async function mountDetail(value: Record<string, unknown>) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(OfferDetail, { props: { offer: value as never }, global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } } });
  await flushPromises();
  return wrapper;
}

describe("OfferDetail, annonce chez l'employeur (docs/20 §2)", () => {
  it("lien vérifié affiché avec sa source", async () => {
    const wrapper = await mountDetail(
      offer({ employer_url: "https://exemple.ch/jobs/2", employer_url_source: "ats", employer_status: "found", employer_checked_at: "2026-10-07T08:00:00Z" }),
    );
    expect(wrapper.find("[data-test=employer]").attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(wrapper.find("[data-test=employer-line]").text()).toContain("via son outil de recrutement");
  });

  it("recherche à la demande, puis « pas trouvée »", async () => {
    POST.mockResolvedValue({ data: offer({ employer_status: "not_found", employer_checked_at: "2026-10-07T08:00:00Z" }) });
    const wrapper = await mountDetail(offer());
    // Dans le « ⋯ » de la partie Entreprise (docs/74).
    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=find-employer]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/employer", { params: { path: { offer_id: 4 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
    // L'offre rechargée affiche l'état, une seule fois.
    await wrapper.setProps({ offer: offer({ employer_status: "not_found", employer_checked_at: "2026-10-07T08:00:00Z" }) as never });
    const line = wrapper.find("[data-test=employer-line]");
    expect(line.text().match(/Pas trouvée/g)).toHaveLength(1);
    await wrapper.find("[data-test=company-more]").trigger("click");
    expect(wrapper.find("[data-test=find-employer]").text()).toBe("Chercher à nouveau chez l'employeur");
  });

  it("agence, ou lien employeur déjà donné par jobup", async () => {
    expect((await mountDetail(offer({ employer_status: "agency" }))).text()).toContain("employeur non indiqué");
    const known = await mountDetail(offer({ apply_kind: "external", apply_url: "https://exemple.ch/postuler" }));
    expect(known.find("[data-test=employer-line]").exists()).toBe(false);
  });
});

describe("OfferDetail, l'essentiel en haut (docs/21 §5)", () => {
  it("tête : « Préparer » et « Écarter », le reste dans ⋯, le lien de l'annonce dans « Le poste » (étape 6b)", async () => {
    const wrapper = await mountDetail(offer());
    const triage = wrapper.find("[data-test=triage]");
    expect(triage.findAll("a")).toHaveLength(1);
    expect(triage.find("[data-test=prepare]").text()).toBe("Préparer ma candidature");
    expect(triage.find("[data-test=offer-discard]").text()).toBe("Écarter");
    const apply = wrapper.find("[data-test=section-ad] [data-test=apply]");
    expect(apply.attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(apply.text()).toContain("Postuler sur Indeed");
    // « Voir sur Indeed » serait le même lien que « Postuler sur Indeed » : il n'apparaît pas.
    expect(wrapper.text()).not.toContain("Voir sur Indeed");
    expect(wrapper.find("[data-test=mark-applied]").exists()).toBe(false);
    await wrapper.find("[data-test=more]").trigger("click");
    for (const key of ["mark-applied", "later", "ignore", "flag-expired"]) {
      expect(wrapper.find(`[data-test=${key}]`).exists()).toBe(true);
    }
    expect(wrapper.find("[data-test=ignore]").text()).toContain("Écarter");
    // Chercher chez l'employeur est rangé dans la partie Entreprise (docs/74).
    expect(wrapper.find("[data-test=find-employer]").exists()).toBe(false);
  });

  it("la correspondance, « Le poste » résumé par jobA1, puis Entreprise et Contacts repliés (maquette Offre)", async () => {
    const wrapper = await mountDetail(
      offer({
        employer_url: "https://exemple.ch/jobs/2",
        employer_status: "found",
        score: 88,
        score_stale: true,
        summary_role: "Architecte cloud",
        summary_asks: "AWS",
        summary_offers: "80-100 %",
        rate_min: 80,
        rate_max: 100,
        remote: "hybrid",
        remote_days: 2,
        strengths: [
          { text: "Kubernetes : plateforme de 40 services en production.", chunk_ids: [1] },
          { text: "Terraform : infrastructure sur Azure et AWS.", chunk_ids: [1] },
          { text: "CI/CD : déploiements continus.", chunk_ids: [1] },
          { text: "Un quatrième point de trop.", chunk_ids: [1] },
        ],
        doubts: [{ kind: "permanent", text: "Annonce permanente : vue depuis 38 jours", excerpt: null }],
        filter_reasons: ["Type : stage"],
        description: "Missions. ".repeat(60),
      }),
    );
    // « ← » vient en premier, au-dessus du logo et du titre (règles §2).
    expect(wrapper.find("[data-test=offer-detail]").element.firstElementChild!.getAttribute("data-test")).toBe("back-detail");
    // Les étiquettes : seulement ce qui est connu, et la date sans « il y a » (dates.ts).
    const tags = wrapper.findAll("[data-test=offer-tags] li").map((li) => li.text());
    expect(tags).toEqual(["80–100 %", "Contrat non précisé", "Télétravail 2 j", "Reçue le 5 octobre"]);
    // Le mot en titre, le chiffre seul dans l'anneau (D12, maquette Offre).
    expect(wrapper.find("[data-test=match-title]").text()).toBe("Très proche de ton profil");
    expect(wrapper.find("[data-test=match-sub]").text()).toBe("Selon ton profil et tes préférences");
    expect(wrapper.find("[data-test=section-for-you] .score-ring").text()).toBe("88");
    const lines = wrapper.findAll("[data-test=match-lines] li");
    expect(lines.map((li) => li.classes("ok"))).toEqual([true, true, true]);
    expect(lines[0]!.text()).toContain("Kubernetes");
    // Le détail de la note : trois puces au plus, le mot clé en gras en tête.
    const points = wrapper.findAll("[data-test=strengths] li");
    expect(points).toHaveLength(3);
    expect(points[0]!.find("strong").text()).toBe("Kubernetes :");
    expect(wrapper.find("[data-test=score-note]").text()).toBe("Ton profil a changé depuis : note à refaire.");
    // Le poste : « Résumé par jobA1 » au-dessus du résumé (O6), l'annonce complète à la demande.
    expect(wrapper.find("[data-test=summary-by]").text()).toBe("Résumé par jobA1");
    expect(wrapper.findAll("[data-test=summary]")).toHaveLength(3);
    expect(wrapper.find("[data-test=description]").exists()).toBe(false);
    const marks = wrapper.findAll("[data-test=facts] li").map((li) => li.find(".fact-mark [data-icon]").attributes("data-icon"));
    expect(marks).toEqual(["alert", "x-circle"]);
    // L'annonce chez l'employeur est le lien ; celle d'Indeed, seule autre, s'affiche directement (docs/76 §3).
    expect(wrapper.find("[data-test=ad-more]").exists()).toBe(false);
    expect(wrapper.find("[data-test=source-indeed]").text()).toContain("Voir sur Indeed");
    await wrapper.find("[data-test=read-more]").trigger("click");
    expect(wrapper.find("[data-test=description]").exists()).toBe(true);
    expect(wrapper.find("[data-test=read-more]").exists()).toBe(false);
    // L'entreprise et les contacts, repliés, avec leur résumé (règles §3.4) ; plus de « Contacts » dans ⋯ (O9).
    const rows = wrapper.findAll(".detail-disclosure > .disclosure-row");
    expect(rows.map((r) => r.attributes("aria-expanded"))).toEqual(["false", "false"]);
    expect(wrapper.find("[data-test=company-section] .disclosure-value").text()).toBe("Exemple SA");
    expect(wrapper.find("[data-test=contacts-section]").exists()).toBe(true);
    expect(wrapper.text()).not.toMatch(/fois, depuis le/);
  });

  it("annonce trouvée chez l'employeur : « Postuler chez l'employeur »", async () => {
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/jobs/2", employer_status: "found" }));
    const button = wrapper.find("[data-test=employer]");
    expect(button.attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(button.text()).toContain("Postuler chez l'employeur");
  });
});

describe("OfferDetail, partie Entreprise rangée (docs/74)", () => {
  it("l'adresse dans la partie Entreprise, les actions dans son « ⋯ », « Adresse inconnue · Ajouter »", async () => {
    const known = await mountDetail(offer({ company_address: "Rue 1\n1201 Genève", company_address_source: "registry" }));
    expect(known.find("[data-test=address] dd").text()).toContain("Rue 1, 1201 Genève");
    expect(known.find("[data-test=add-address]").exists()).toBe(false);
    const section = known.find("[data-test=company-section]");
    await section.find("[data-test=company-more]").trigger("click");
    const labels = section.findAll("[role=menuitem]").map((item) => item.text());
    expect(labels).toEqual(["Modifier l'adresse", "Chercher l'adresse", "Chercher l'offre chez l'employeur"]);

    const missing = await mountDetail(offer());
    expect(missing.find("[data-test=address] dd").text().replace(/\s+/g, " ")).toBe("Adresse inconnue · Ajouter");
    await missing.find("[data-test=add-address]").trigger("click");
    expect(missing.find("[data-test=address-input]").exists()).toBe(true);
  });
});

describe("la note expliquée (docs/121 §C.1-3)", () => {
  it("la phrase « pourquoi », le niveau en étiquette, « Je l'ai » seulement sur un manque sans bloc", async () => {
    POST.mockResolvedValue({ data: { chunk_id: 9, score: 84 } });
    const wrapper = await mountDetail(
      offer({
        score: 72,
        summary_role: "Exploiter le cloud",
        summary_asks: "Terraform, 8 ans",
        summary_offers: "100 %",
        why: "Ton expérience AWS colle ; il manque Terraform.",
        level: "above",
        level_detail: "8 ans demandés, ton profil en montre 3.",
        strengths: [{ text: "AWS en production", chunk_ids: [1] }],
        gaps: [
          { text: "Pas de Terraform", chunk_ids: [] },
          { text: "Préférence : pas d'astreintes", chunk_ids: [2] },
        ],
      }),
    );
    expect(wrapper.find("[data-test=score-why]").text()).toContain("Ton expérience AWS colle ; il manque Terraform.");
    expect(wrapper.find("[data-test=score-level]").text()).toBe("Niveau au-dessus");
    expect(wrapper.find("[data-test=score-level] [data-test=hover-note]").attributes("aria-description")).toBe(
      "8 ans demandés, ton profil en montre 3.",
    );
    const gaps = wrapper.findAll("[data-test=gaps] li");
    expect(gaps[0]!.find("[data-test=gap-fill]").exists()).toBe(true);
    expect(gaps[1]!.find("[data-test=gap-fill]").exists()).toBe(false);

    await gaps[0]!.find("[data-test=gap-fill]").trigger("click");
    expect((wrapper.find("[data-test=gap-fill-title]").element as HTMLInputElement).value).toBe("Terraform");
    await wrapper.find("[data-test=gap-fill-content]").setValue("Trois ans d'infrastructure en Terraform.");
    await wrapper.find("[data-test=gap-fill-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/gap-block", {
      params: { path: { offer_id: 4 } },
      body: { title: "Terraform", content: "Trois ans d'infrastructure en Terraform." },
    });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });
});

describe("OfferDetail sur téléphone, une sous-page (maquette Offre, docs/139 étape 6a)", () => {
  const phone = () => vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px") || media.includes("599px"), addEventListener() {}, removeEventListener() {} }));

  it("en-tête retour, Sauvegarder, « ⋯ », Partager ; en bas « Écarter » et « Préparer ma candidature »", async () => {
    phone();
    const wrapper = await mountDetail(offer({ score: 78, why: "Kubernetes, Terraform et CI/CD : dans ton profil.", summary_role: "x" }));
    expect(wrapper.find("[data-test=triage]").exists()).toBe(false);
    const head = wrapper.find("[data-test=offer-subhead]");
    expect(head.find("[data-test=back-detail]").attributes("aria-label")).toBe("Retour aux candidatures");
    await head.find("[data-test=back-detail]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
    // Le signet est l'état « Plus tard » (O2).
    const save = head.find("[data-test=offer-save]");
    expect(save.attributes("aria-pressed")).toBe("false");
    await save.trigger("click");
    expect(wrapper.emitted("status")?.[0]).toEqual(["later"]);
    // Partager : le lien de l'annonce, jamais l'adresse jobA1.
    expect(head.find("[data-test=offer-share]").exists()).toBe(true);
    const bar = wrapper.find("[data-test=offer-bar]");
    expect(bar.find("[data-test=offer-discard]").text()).toBe("Écarter");
    expect(bar.find("[data-test=prepare]").text()).toBe("Préparer ma candidature");
    await bar.find("[data-test=offer-discard]").trigger("click");
    expect(wrapper.emitted("status")?.[1]).toEqual(["ignored"]);
    // La note et sa phrase restent dans la carte « Pourquoi » ; la correction passe par la feuille « ⋯ ».
    expect(wrapper.find("[data-test=section-for-you]").text()).toContain("Kubernetes, Terraform et CI/CD : dans ton profil.");
    expect(wrapper.find("[data-test=section-for-you] [data-test=score-correction-open]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });

  it("le signet est plein pour une offre gardée pour plus tard ; un clic la remet à examiner", async () => {
    phone();
    const wrapper = await mountDetail(offer({ status: "later" }));
    const save = wrapper.find("[data-test=offer-save]");
    expect(save.attributes("aria-pressed")).toBe("true");
    await save.trigger("click");
    expect(wrapper.emitted("status")?.[0]).toEqual(["to_review"]);
    vi.unstubAllGlobals();
  });

  it("partage le lien public par la feuille du téléphone, sinon le copie", async () => {
    phone();
    const shareFn = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, share: shareFn });
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/poste" }));
    await wrapper.find("[data-test=offer-share]").trigger("click");
    expect(shareFn).toHaveBeenCalledWith(expect.objectContaining({ url: "https://exemple.ch/poste" }));
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, share: undefined, clipboard: { writeText } });
    await wrapper.find("[data-test=offer-share]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("https://exemple.ch/poste");
    expect(wrapper.find("[data-test=offer-said]").text()).toBe("Lien copié.");
    vi.unstubAllGlobals();
  });

  it("une offre expirée mène aux offres proches ; en préparation, « Reprendre la lettre »", async () => {
    phone();
    const expired = await mountDetail(offer({ expired_at: "2026-10-30T10:00:00Z" }));
    expect(expired.find("[data-test=nearby]").text()).toBe("Voir des offres proches");
    expect(expired.find("[data-test=prepare]").exists()).toBe(false);
    const preparing = await mountDetail(offer({ status: "preparing" }));
    expect(preparing.find("[data-test=prepare]").text()).toBe("Reprendre la lettre");
    vi.unstubAllGlobals();
  });

  it("la feuille « ⋯ » : Écarter, Marquer comme envoyée, puis les actions de la fiche, sans « Plus tard »", async () => {
    phone();
    const wrapper = await mountDetail(offer({ score: 78, why: "x", summary_role: "x" }));
    await wrapper.find("[data-test=detail-more]").trigger("click");
    const sheet = wrapper.find("[data-test=offer-actions]");
    const titles = sheet.findAll(".grouped-row-title").map((t) => t.text());
    expect(titles.slice(0, 2)).toEqual(["Écarter l'offre", "Marquer comme envoyée"]);
    expect(titles).toContain("Signaler comme expirée");
    expect(titles).toContain("Cette note ne me correspond pas");
    expect(titles).not.toContain("Plus tard");
    await sheet.find("[data-test=offer-action-score-correction-menu] button").trigger("click");
    expect(wrapper.find("[data-test=score-correction-sheet] .score-correction-card.bare").exists()).toBe(true);
    vi.unstubAllGlobals();
  });

  it("une offre où j'ai postulé : pas de barre", async () => {
    phone();
    const wrapper = await mountDetail(offer({ status: "applied" }));
    expect(wrapper.find("[data-test=offer-bar]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });
});
