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

describe("OfferDetail, annonce chez l’employeur (docs/20 §2)", () => {
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
    expect(wrapper.find("[data-test=find-employer]").text()).toBe("Chercher à nouveau chez l’employeur");
  });

  it("agence, ou lien employeur déjà donné par jobup", async () => {
    expect((await mountDetail(offer({ employer_status: "agency" }))).text()).toContain("employeur non indiqué");
    const known = await mountDetail(offer({ apply_kind: "external", apply_url: "https://exemple.ch/postuler" }));
    expect(known.find("[data-test=employer-line]").exists()).toBe(false);
  });
});

describe("OfferDetail, l’essentiel en haut (docs/21 §5)", () => {
  it("tête : « Préparer » et « Écarter », le reste dans ⋯, le lien de l’annonce dans « Le poste » (étape 6b)", async () => {
    const wrapper = await mountDetail(offer());
    const triage = wrapper.find("[data-test=triage]");
    expect(triage.findAll("a")).toHaveLength(1);
    expect(triage.find("[data-test=prepare]").text()).toBe("Préparer ma candidature");
    // Il lance l'écriture de la lettre et du CV dès l'arrivée (MODIFICATIONS du 9 novembre, §7 n° 1).
    expect(triage.find("[data-test=prepare]").attributes("href")).toMatch(/\/preparer\?ecrire=1$/);
    expect(triage.find("[data-test=offer-discard]").text()).toBe("Écarter");
    // Lot 15.2 : « J'ai déjà postulé » à droite de « Écarter », le parcours « Marquer comme envoyée ».
    const already = triage.find("[data-test=offer-already-applied]");
    expect(already.text()).toBe("J’ai déjà postulé");
    await already.trigger("click");
    expect(wrapper.emitted("applied")).toHaveLength(1);
    const apply = wrapper.find("[data-test=section-ad] [data-test=apply]");
    expect(apply.attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(apply.text()).toContain("Voir l’annonce sur Indeed");
    expect(wrapper.text()).not.toContain("Postuler sur");
    // Un seul lien visible vers l'adresse de l'annonce, hors menu « … » (PR 25).
    expect(wrapper.findAll('a[href="https://ch.indeed.com/viewjob?jk=1"]')).toHaveLength(1);
    // « Voir sur Indeed » serait le même lien : il n'apparaît pas.
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
    // L’entreprise en champs ouverts (PR 33, point 4), les contacts repliés (règles §3.4) ; plus de « Contacts » dans ⋯ (O9).
    const rows = wrapper.findAll(".detail-disclosure > .disclosure-row");
    expect(rows.map((r) => r.attributes("aria-expanded"))).toEqual(["false"]);
    expect(wrapper.find("[data-test=company-section] .block-field-value").text()).toBe("Exemple SA");
    expect(wrapper.find("[data-test=contacts-section]").exists()).toBe(true);
    expect(wrapper.text()).not.toMatch(/fois, depuis le/);
  });

  it("annonce trouvée chez l’employeur : « Voir l’annonce sur le site de l’employeur »", async () => {
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/jobs/2", employer_status: "found" }));
    const button = wrapper.find("[data-test=employer]");
    expect(button.attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(button.text()).toContain("Voir l’annonce sur le site de l’employeur");
  });
});

describe("OfferDetail, partie Entreprise rangée (docs/74)", () => {
  it("l’adresse dans la partie Entreprise, les actions dans son « ⋯ », « Non renseignée » et « Compléter »", async () => {
    const known = await mountDetail(offer({ company_address: "Rue 1\n1201 Genève", company_address_source: "registry" }));
    // PR 33 (4) : le libellé au-dessus, la valeur en gras dessous, copier à droite ; ni bandeau ni ligne repliable.
    expect(known.find("[data-test=company-section] .disclosure-row").exists()).toBe(false);
    expect(known.find("[data-test=company-section] h3").text()).toBe("L’entreprise");
    expect(known.find("[data-test=address] .block-field-label").text()).toBe("Adresse");
    expect(known.find("[data-test=address] .block-field-value").text()).toBe("Rue 1, 1201 Genève");
    expect(known.find("[data-test=address] [data-test=address-copy]").exists()).toBe(true);
    expect(known.find("[data-test=add-address]").exists()).toBe(false);
    const section = known.find("[data-test=company-section]");
    await section.find("[data-test=company-more]").trigger("click");
    const labels = section.findAll("[role=menuitem]").map((item) => item.text());
    expect(labels).toEqual(["Modifier l’adresse", "Chercher l’adresse", "Chercher l’offre chez l’employeur"]);

    const missing = await mountDetail(offer());
    expect(missing.find("[data-test=address] .block-field-value").text()).toBe("Non renseignée");
    expect(missing.find("[data-test=add-address]").text()).toBe("Compléter");
    await missing.find("[data-test=add-address]").trigger("click");
    expect(missing.find("[data-test=address-input]").exists()).toBe(true);
  });
});

describe("la note expliquée (docs/121 §C.1-3)", () => {
  it("la phrase « pourquoi », le niveau en étiquette, « Je l’ai » seulement sur un manque sans bloc", async () => {
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
          { text: "Préférence : pas d’astreintes", chunk_ids: [2] },
        ],
        // Le texte complet est lu : les manques s'affichent (la note n'est pas provisoire).
        description: "Texte complet de l’annonce.",
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
    await wrapper.find("[data-test=gap-fill-content]").setValue("Trois ans d’infrastructure en Terraform.");
    await wrapper.find("[data-test=gap-fill-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/gap-block", {
      params: { path: { offer_id: 4 } },
      body: { title: "Terraform", content: "Trois ans d’infrastructure en Terraform." },
    });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });
});

describe("OfferDetail sur téléphone, une sous-page (maquette Offre, docs/139 étape 6a)", () => {
  const phone = () => vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px") || media.includes("599px"), addEventListener() {}, removeEventListener() {} }));

  it("en-tête retour, Sauvegarder, « ⋯ » (lot 18 : Partager passe dans la feuille) ; en bas « Écarter » (§10.1, 9 novembre) et « Préparer ma candidature »", async () => {
    phone();
    const wrapper = await mountDetail(offer({ score: 78, why: "Kubernetes, Terraform et CI/CD : dans ton profil.", summary_role: "x" }));
    expect(wrapper.find("[data-test=triage]").exists()).toBe(false);
    const head = wrapper.find("[data-test=offer-subhead]");
    expect(head.find("[data-test=back-detail]").attributes("aria-label")).toBe("Retour aux candidatures");
    await head.find("[data-test=back-detail]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
    // Le signet est l'état « Gardée » (O2, PR 46).
    const save = head.find("[data-test=offer-save]");
    expect(save.attributes("aria-pressed")).toBe("false");
    await save.trigger("click");
    expect(wrapper.emitted("status")?.[0]).toEqual(["later"]);
    // Lot 18 (maquette Offre) : l'en-tête n'a plus Partager.
    expect(head.find("[data-test=offer-share]").exists()).toBe(false);
    const bar = wrapper.find("[data-test=offer-bar]");
    expect(bar.find("[data-test=offer-discard]").text()).toBe("Écarter");
    expect(bar.find("[data-test=offer-discard]").classes()).toContain("action-2");
    expect(bar.find("[data-test=prepare]").text()).toBe("Préparer ma candidature");
    await bar.find("[data-test=offer-discard]").trigger("click");
    expect(wrapper.emitted("status")?.[1]).toEqual(["ignored"]);
    // §10.1 (9 novembre) : la carte de la note ne garde que l'anneau, le verdict et « Voir la compatibilité » ; la
    // phrase passe dans la feuille (« Comment la note est calculée ») ; la correction passe par la feuille « ⋯ ».
    // Sans l'annonce complète, le lien sous la bande s'appelle « Le détail de la note » (corrections du 9 novembre).
    expect(wrapper.find("[data-test=section-for-you] [data-test=compat-open]").text()).toBe("Le détail de la note");
    expect(wrapper.findComponent({ name: "OfferCompatSheet" }).props("how")).toContain("Kubernetes, Terraform et CI/CD : dans ton profil.");
    expect(wrapper.find("[data-test=section-for-you] [data-test=score-correction-open]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });

  it("§10.1 : « Voir la compatibilité » ouvre la feuille ; points « Critère : valeur », phrase entière sans libellé", async () => {
    phone();
    const wrapper = await mountDetail(
      offer({
        score: 76,
        description: "Annonce complète.",
        why: "Kubernetes et Terraform : dans ton profil.",
        strengths: [{ text: "Lieu : Lausanne, 20 min" }, { text: "Ton expérience en CI/CD correspond" }],
        gaps: [{ text: "Langue : allemand courant demandé" }],
      }),
    );
    const sheet = wrapper.findComponent({ name: "OfferCompatSheet" });
    expect(sheet.props("open")).toBe(false);
    // Prompt du 10 novembre, PR 15 : sur téléphone, le lien s'appelle « Le détail de la note », note provisoire ou non.
    expect(wrapper.find("[data-test=compat-open]").text()).toBe("Le détail de la note");
    await wrapper.find("[data-test=compat-open]").trigger("click");
    expect(sheet.props("open")).toBe(true);
    expect(sheet.props("strengths")).toEqual([
      { key: "Lieu", value: "Lausanne, 20 min" },
      { key: "", value: "Ton expérience en CI/CD correspond" },
    ]);
    expect(sheet.props("gaps")).toEqual([{ key: "Langue", value: "allemand courant demandé" }]);
    expect(sheet.props("how")).toContain("Kubernetes et Terraform : dans ton profil.");
    vi.unstubAllGlobals();
  });

  it("le signet est plein pour une offre gardée ; un clic la remet à examiner", async () => {
    phone();
    const wrapper = await mountDetail(offer({ status: "later" }));
    const save = wrapper.find("[data-test=offer-save]");
    expect(save.attributes("aria-pressed")).toBe("true");
    // Le libellé et le nom accessible du signet : « Garder » (PR 46), plus « Garder pour plus tard ».
    expect([save.attributes("aria-label"), save.attributes("data-label")]).toEqual(["Garder", "Garder"]);
    await save.trigger("click");
    expect(wrapper.emitted("status")?.[0]).toEqual(["to_review"]);
    vi.unstubAllGlobals();
  });

  it("« Partager l’annonce » dans la feuille « ⋯ » : le lien public par la feuille du téléphone, sinon le copie", async () => {
    phone();
    const shareFn = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, share: shareFn });
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/poste" }));
    const share = async () => {
      await wrapper.find("[data-test=detail-more]").trigger("click");
      await wrapper.find("[data-test=offer-action-share] button").trigger("click");
    };
    await share();
    expect(shareFn).toHaveBeenCalledWith(expect.objectContaining({ url: "https://exemple.ch/poste" }));
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, share: undefined, clipboard: { writeText } });
    await share();
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
    expect(preparing.find("[data-test=prepare]").attributes("href")).toMatch(/\/preparer$/);
    vi.unstubAllGlobals();
  });

  it("la feuille « ⋯ » : Écarter, J’ai déjà postulé (lot 15.2), puis les actions de la fiche, sans « Garder »", async () => {
    phone();
    const wrapper = await mountDetail(offer({ score: 78, why: "x", summary_role: "x" }));
    await wrapper.find("[data-test=detail-more]").trigger("click");
    const sheet = wrapper.find("[data-test=offer-actions]");
    const titles = sheet.findAll(".grouped-row-title").map((t) => t.text());
    expect(titles.slice(0, 2)).toEqual(["Écarter l’offre", "J’ai déjà postulé"]);
    expect(titles).toContain("Signaler comme expirée");
    expect(titles).toContain("Cette note ne me correspond pas");
    expect(titles).not.toContain("Garder");
    await sheet.find("[data-test=offer-action-score-correction-menu] button").trigger("click");
    expect(wrapper.find("[data-test=score-correction-sheet] .score-correction-card.bare").exists()).toBe(true);
    vi.unstubAllGlobals();
  });

  it("une offre où j’ai postulé : pas de barre", async () => {
    phone();
    const wrapper = await mountDetail(offer({ status: "applied" }));
    expect(wrapper.find("[data-test=offer-bar]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });
});

describe("OfferDetail sur ordinateur, deux colonnes (lot 13.1)", () => {
  const desktop = () => vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("1024px"), addEventListener() {}, removeEventListener() {} }));
  afterEach(() => vi.unstubAllGlobals());

  it("la note et le poste à gauche ; « L’offre en bref » à droite, en <dl>, avec le lien vers l’annonce", async () => {
    desktop();
    const wrapper = await mountDetail(offer({ score: 60, snippet: "Kubernetes", employment_type: null, rate_min: null, rate_max: null }));
    const main = wrapper.find("[data-test=detail-columns-main]");
    expect(main.find("[data-test=section-for-you]").exists()).toBe(true);
    expect(main.find("[data-test=section-ad]").exists()).toBe(true);
    // La lecture de l'annonce complète (prompt du 10 novembre) reste dans la note.
    expect(main.find("[data-test=section-for-you] [data-test=text-reading]").exists()).toBe(true);
    const aside = wrapper.find("aside[data-test=detail-columns-aside]");
    expect(aside.attributes("aria-label")).toBe("L’offre en bref");
    const rows = aside.findAll("dl > div").map((row) => [row.find("dt").text(), row.find("dd").text()]);
    expect(rows.map((r) => r[0])).toEqual(["Lieu", "Contrat", "Taux d’activité", "Reçue"]);
    expect(rows[1]![1]).toBe("Non précisé");
    expect(rows[3]![1]).toMatch(/, par une alerte e-mail$/);
    const brief = aside.find("[data-test=brief-link]");
    expect(brief.attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(brief.text()).toContain("Voir l’annonce sur Indeed");
    // Un seul lien visible vers l'annonce sur ordinateur aussi : celui de « L'offre en bref » (PR 25).
    expect(wrapper.findAll('a[href="https://ch.indeed.com/viewjob?jk=1"]')).toHaveLength(1);
    // Les étiquettes du haut restent.
    expect(wrapper.find("[data-test=tag-contract]").text()).toBe("Contrat non précisé");
  });

  it("la note en carte d’information avec « Voir la compatibilité », qui ouvre le panneau (§2.1 du 9 novembre)", async () => {
    desktop();
    const wrapper = await mountDetail(offer({ score: 60, snippet: "Kubernetes" }));
    const note = wrapper.find("[data-test=section-for-you]");
    expect(note.find("[data-test=match-lines]").exists()).toBe(false);
    expect(note.find("[data-test=note-detail]").exists()).toBe(false);
    const open = note.get("[data-test=compat-open]");
    expect(open.text()).toContain("Voir la compatibilité");
    expect(open.attributes("aria-haspopup")).toBe("dialog");
    await open.trigger("click");
    expect(wrapper.find("[data-test=compat-sheet]").exists()).toBe(true);
  });

  it("sous 1 024 px, une seule colonne", async () => {
    const wrapper = await mountDetail(offer());
    expect(wrapper.find("[data-test=detail-columns]").exists()).toBe(false);
    expect(wrapper.find("[data-test=offer-brief]").exists()).toBe(false);
  });
});

describe("OfferDetail, langues (prompt du 10 novembre, PR 17)", () => {
  it("une langue exigée au niveau non renseigné s’affiche « à vérifier »", async () => {
    const wrapper = await mountDetail(offer({ languages_to_check: ["anglais", "allemand"] }));
    const facts = wrapper.findAll("[data-test=facts] li").map((li) => li.text());
    expect(facts).toContain("Langue à vérifier : anglais");
    expect(facts).toContain("Langue à vérifier : allemand");
  });

  it("rien à vérifier : aucune ligne de langue", async () => {
    const wrapper = await mountDetail(offer());
    expect(wrapper.text()).not.toContain("Langue à vérifier");
  });
});

describe("OfferDetail, passages surlignés dans « Le poste » (lot du 11 novembre au soir, PR 47)", () => {
  const text = "Vous exploitez nos clusters Kubernetes.\nVous écrivez l’infrastructure avec Terraform.";

  it("les passages retrouvés sont surlignés, la légende les compte ; le texte de l'annonce ne change pas", async () => {
    const wrapper = await mountDetail(offer({ description: text, passages: ["clusters Kubernetes", "l'infrastructure avec Terraform"] }));
    const shown = wrapper.find("[data-test=description]");
    expect(shown.findAll("mark").map((m) => m.text())).toEqual(["clusters Kubernetes", "l’infrastructure avec Terraform"]);
    expect(shown.element.textContent).toBe(text);
    expect(wrapper.find("[data-test=passage-legend]").text()).toBe("2 passages qui correspondent à ton profil");
  });

  it("un seul passage : la légende au singulier", async () => {
    const wrapper = await mountDetail(offer({ description: text, passages: ["clusters Kubernetes"] }));
    expect(wrapper.find("[data-test=passage-legend]").text()).toBe("1 passage qui correspond à ton profil");
  });

  it("aucun passage (note plus ancienne) ou passage absent du texte affiché : ni surlignage ni légende", async () => {
    for (const passages of [undefined, [], ["une citation inventée"]]) {
      const wrapper = await mountDetail(offer({ description: text, passages }));
      expect(wrapper.find("[data-test=description] mark").exists()).toBe(false);
      expect(wrapper.find("[data-test=passage-legend]").exists()).toBe(false);
    }
  });

  it("résumé affiché : la légende ne compte que ce qui est surligné à l'écran, puis l'annonce dépliée", async () => {
    const wrapper = await mountDetail(offer({ description: text, passages: ["clusters Kubernetes"], summary_role: "Faire tourner la plateforme.", score: 80, why: "x" }));
    expect(wrapper.find("[data-test=passage-legend]").exists()).toBe(false);
    await wrapper.find("[data-test=read-more]").trigger("click");
    expect(wrapper.find("[data-test=description] mark").text()).toBe("clusters Kubernetes");
    expect(wrapper.find("[data-test=passage-legend]").exists()).toBe(true);
  });
});
