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

describe("OfferDetail, recherche d’adresse (audit du 17.11, K6)", () => {
  it("en cours avec le cercle qui tourne ; « trouvée » seulement si l’adresse affichée change", async () => {
    POST.mockResolvedValue({ data: { chosen_uid: "CHE-1", candidates: [] } });
    const wrapper = await mountDetail(offer({ company_address: null, company_address_source: null }));
    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=search-registry]").trigger("click");
    await flushPromises();
    expect(wrapper.emitted("changed")).toHaveLength(1);
    // Jusqu'à la fiche relue, la recherche est encore en cours.
    expect(wrapper.find("[data-test=registry-busy] .offer-busy-ring").exists()).toBe(true);
    await wrapper.setProps({ offer: offer({ company_address: null, company_address_source: null }) as never });
    expect(wrapper.find("[data-test=registry-busy]").exists()).toBe(false);
    // Planche OffreAdresseNonTrouvee (18.11) : « Non renseignée », la pastille grise, « Ajouter l'adresse ».
    expect(wrapper.find("[data-test=address] .block-field-value").text()).toBe("Non renseignée");
    expect(wrapper.find("[data-test=address-not-found]").text()).toBe("Pas trouvée au registre");
    expect(wrapper.find("[data-test=registry]").exists()).toBe(false);
    expect(wrapper.find("[data-test=add-address]").text()).toBe("Ajouter l’adresse");

    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=search-registry]").trigger("click");
    await flushPromises();
    await wrapper.setProps({ offer: offer({ company_address: "Rue du Lac 1\n1000 Lausanne", company_address_source: "registry" }) as never });
    // Planche OffreAdresseTrouvee : l'adresse sur deux lignes, la pastille, « Modifier l'adresse », pas de phrase.
    expect(wrapper.find("[data-test=address-not-found]").exists()).toBe(false);
    expect(wrapper.find("[data-test=address-registry]").text()).toBe("Trouvée au registre du commerce");
    expect(wrapper.find("[data-test=registry]").exists()).toBe(false);
    expect(wrapper.find("[data-test=add-address]").text()).toBe("Modifier l’adresse");
    expect(wrapper.find("#offer-company-title").text()).toBe("L’entreprise");

    // « Site de l'entreprise » : le site relevé sur l'annonce, sans « www. » ; rien pour une adresse qui n'est pas http(s).
    expect(wrapper.find("[data-test=company-website]").exists()).toBe(false);
    await wrapper.setProps({ offer: offer({ company_website: "https://www.alpstack.ch/" }) as never });
    const site = wrapper.find("[data-test=company-website]");
    expect(site.text()).toContain("Site de l’entreprise");
    expect(site.find(".company-site-host").text()).toBe("alpstack.ch");
    expect(site.attributes("href")).toBe("https://www.alpstack.ch/");
    expect(site.attributes("rel")).toBe("noopener noreferrer");
    await wrapper.setProps({ offer: offer({ company_website: "javascript:alert(1)" }) as never });
    expect(wrapper.find("[data-test=company-website]").exists()).toBe(false);

    // Une adresse trouvée sur Internet que le registre ne change pas : la phrase le dit, sans pastille « pas trouvée ».
    const manual = { company_address: "Rue du Lac 1\n1000 Lausanne", company_address_source: "web" };
    await wrapper.setProps({ offer: offer(manual) as never });
    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=search-registry]").trigger("click");
    await flushPromises();
    await wrapper.setProps({ offer: offer(manual) as never });
    expect(wrapper.find("[data-test=registry]").text()).toBe("Aucune nouvelle adresse trouvée.");
    expect(wrapper.find("[data-test=address-not-found]").exists()).toBe(false);
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
  it("l’adresse dans la partie Entreprise, les actions dans son « ⋯ », « Non renseignée » et « Ajouter l’adresse »", async () => {
    const known = await mountDetail(offer({ company_address: "Rue 1\n1201 Genève", company_address_source: "registry" }));
    // PR 33 (4) : le libellé au-dessus, la valeur en gras dessous, copier à droite ; ni bandeau ni ligne repliable.
    expect(known.find("[data-test=company-section] .disclosure-row").exists()).toBe(false);
    expect(known.find("[data-test=company-section] h3").text()).toBe("L’entreprise");
    expect(known.find("[data-test=address] .block-field-label").text()).toBe("Adresse");
    // Planche OffreAdresseTrouvee (18.11) : l'adresse telle qu'enregistrée, sur deux lignes.
    expect(known.find("[data-test=address] .block-field-value").text()).toBe("Rue 1\n1201 Genève");
    expect(known.find("[data-test=address] .address-lines").exists()).toBe(true);
    expect(known.find("[data-test=address] [data-test=address-copy]").exists()).toBe(true);
    expect(known.find("[data-test=add-address]").text()).toBe("Modifier l’adresse");
    const section = known.find("[data-test=company-section]");
    await section.find("[data-test=company-more]").trigger("click");
    const labels = section.findAll("[role=menuitem]").map((item) => item.text());
    expect(labels).toEqual(["Modifier l’adresse", "Chercher l’adresse", "Chercher l’offre chez l’employeur"]);

    const missing = await mountDetail(offer());
    expect(missing.find("[data-test=address] .block-field-value").text()).toBe("Non renseignée");
    expect(missing.find("[data-test=add-address]").text()).toBe("Ajouter l’adresse");
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
    // Le signet est l'état « Plus tard » (O2).
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
    // Sous la bande, le lien s'appelle « Voir la compatibilité », comme sur ordinateur (décision de Kevin du 15.11).
    expect(wrapper.find("[data-test=section-for-you] [data-test=compat-open]").text()).toBe("Voir la compatibilité");
    expect(wrapper.findComponent({ name: "OfferCompatSheet" }).props("how")).toContain("Kubernetes, Terraform et CI/CD : dans ton profil.");
    expect(wrapper.find("[data-test=section-for-you] [data-test=score-correction-open]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });

  it("planche Offre (18.11) : grille Taux · Contrat · Télétravail, date sur la ligne de l'entreprise, passages surlignés, autres offres", async () => {
    phone();
    const { api } = await import("../api/client");
    const others = [
      { id: 7, title: "SRE | PLATEFORME", company: "exemple sa ", location: "Lausanne, VD", rate_min: 100, rate_max: 100, score: 78, status: "to_review", first_seen_at: "2026-10-01T08:00:00Z" },
      { id: 8, title: "Platform Engineer", company: "Exemple SA", location: "Lausanne", rate_min: 80, rate_max: 80, score: 60, status: "applied", first_seen_at: "2026-09-28T08:00:00Z" },
      { id: 4, title: "Ingénieur DevOps", company: "Exemple SA", location: "Lausanne", status: "to_review" },
      { id: 9, title: "Autre", company: "Exemple Services SA", location: "Lausanne", status: "to_review" },
    ];
    vi.mocked(api.GET).mockImplementation((() => Promise.resolve({ data: { items: others, total: 4 } })) as never);
    const wrapper = await mountDetail(
      offer({
        rate_min: 80, rate_max: 100, employment_type: "CDI", remote: "hybrid", remote_days: 2, description: "Texte complet.",
        summary_role: "Automatiser l’infrastructure Kubernetes et les pipelines GitLab CI.",
        strengths: [{ text: "Kubernetes : 40 services.", chunk_ids: [] }, { text: "GitLab CI : pipelines.", chunk_ids: [] }],
      }),
    );
    const cells = wrapper.findAll("[data-test=offer-grid] > div").map((c) => [c.find("dt").text(), c.find("dd").text()]);
    expect(cells).toEqual([["Taux", "80–100 %"], ["Contrat", "CDI"], ["Télétravail", "2 j/sem."]]);
    expect(wrapper.find("[data-test=offer-tags]").exists()).toBe(false);
    expect(wrapper.find("[data-test=detail-meta]").text()).toMatch(/· reçue le 5 oct\.$/);
    // Les compétences des points forts, surlignées dans le résumé ; pas de « Résumé par jobA1 ».
    expect(wrapper.findAll("[data-test=summary] mark").map((m) => m.text())).toEqual(["Kubernetes", "GitLab CI"]);
    expect(wrapper.find("[data-test=summary]").text()).toBe("Automatiser l’infrastructure Kubernetes et les pipelines GitLab CI.");
    expect(wrapper.find("[data-test=summary-by]").exists()).toBe(false);
    expect(wrapper.find("[data-test=summary-legend]").text()).toBe("2 passages qui correspondent à ton profil");
    // Les offres de la même entreprise seulement (casse et espaces ignorés), sans l'offre ouverte.
    expect(api.GET).toHaveBeenCalledWith("/api/offers", { params: { query: { q: "Exemple SA", view: "all", sort: "recent", limit: 50 } } });
    const card = wrapper.find("[data-test=company-offers]");
    expect(card.find("h3").text()).toBe("Autres offres chez Exemple SA · 2");
    const rows = card.findAll("[data-test=company-offer]");
    expect(rows.map((r) => r.find("b").text())).toEqual(["SRE · Plateforme", "Platform Engineer"]);
    expect(rows[0]!.text()).toContain("Lausanne · 100 % · 1 oct.");
    expect(rows[0]!.find(".company-offer-pill").text()).toBe("Note 78");
    expect(rows[1]!.find(".company-offer-pill").text()).toBe("Envoyée");
    expect(rows[0]!.attributes("href")).toBe("/candidatures/offres/7");
    vi.unstubAllGlobals();
  });

  it("planche Offre : sans point fort reconnu ni autre offre, ni légende ni carte ; une valeur inconnue le dit", async () => {
    phone();
    const wrapper = await mountDetail(offer({ summary_role: "Un poste.", strengths: [] }));
    expect(wrapper.find("[data-test=summary] mark").exists()).toBe(false);
    expect(wrapper.find("[data-test=summary-legend]").exists()).toBe(false);
    expect(wrapper.find("[data-test=company-offers]").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=offer-grid] dd").map((d) => d.text())).toEqual(["Non précisé", "Non précisé", "Non précisé"]);
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
    // Sur téléphone, le lien s'appelle « Voir la compatibilité », note provisoire ou non (décision de Kevin du 15.11).
    expect(wrapper.find("[data-test=compat-open]").text()).toBe("Voir la compatibilité");
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

  it("le signet est plein pour une offre gardée pour plus tard ; un clic la remet à examiner", async () => {
    phone();
    const wrapper = await mountDetail(offer({ status: "later" }));
    const save = wrapper.find("[data-test=offer-save]");
    expect(save.attributes("aria-pressed")).toBe("true");
    await save.trigger("click");
    expect(wrapper.emitted("status")?.[0]).toEqual(["to_review"]);
    vi.unstubAllGlobals();
  });

  it("« Partager » dans la feuille « ⋯ » : le lien public par la feuille du téléphone, sinon le copie", async () => {
    phone();
    const shareFn = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, share: shareFn });
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/poste" }));
    const share = async () => {
      await wrapper.find("[data-test=detail-more]").trigger("click");
      await wrapper.find("[data-test=offer-action-share]").trigger("click");
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

  it("offre expirée (planche OffreExpiree, 18.11) : la carte, « Écrire quand même », les offres proches dans ⋯", async () => {
    phone();
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-20T09:00:00Z"));
    const expired = await mountDetail(
      offer({ expired_at: "2026-11-17T10:00:00Z", expiry_source: "page", links: [{ source: "jobup", url: "https://www.alpstack.ch/jobs/1" }] }),
    );
    const card = expired.get("[data-test=expired]");
    expect(card.get(".expired-pill").text()).toBe("Offre expirée");
    expect(card.get(".expired-title").text()).toBe("L’annonce n’est plus en ligne");
    expect(card.get(".expired-text").text()).toBe("Vérifiée le 17 nov. sur alpstack.ch. Tu peux encore écrire à l’entreprise.");
    const bar = expired.get("[data-test=offer-bar]");
    expect(bar.get("[data-test=offer-discard]").text()).toBe("Écarter");
    expect(bar.get("[data-test=prepare]").text()).toBe("Écrire quand même");
    expect(bar.get("[data-test=prepare]").attributes("href")).toMatch(/\/preparer\?ecrire=1$/);
    // Kevin, 18.11 : « Voir des offres proches » reste, dans le « ⋯ ».
    await expired.find("[data-test=detail-more]").trigger("click");
    await flushPromises();
    const titles = expired.get("[data-test=offer-actions]").findAll(".offer-action").map((t) => t.text());
    expect(titles).toContain("Voir des offres proches");
    vi.useRealTimers();
    // Une expiration supposée garde sa phrase, sans le titre de la planche.
    const guessed = await mountDetail(offer({ expired_at: "2026-11-17T10:00:00Z", expiry_source: "age" }));
    expect(guessed.find("[data-test=expired] .expired-title").exists()).toBe(false);
    expect(guessed.get("[data-test=expired] .expired-text").text()).toMatch(/^Probablement expirée.*Tu peux encore écrire à l’entreprise\.$/);
    const preparing = await mountDetail(offer({ status: "preparing" }));
    expect(preparing.find("[data-test=prepare]").text()).toBe("Reprendre la lettre");
    expect(preparing.find("[data-test=prepare]").attributes("href")).toMatch(/\/preparer$/);
    vi.unstubAllGlobals();
  });

  it("la feuille « ⋯ » (ActionsOffre, §45) : J’ai déjà postulé, les actions de la fiche, puis Écarter en dernier ; croix, pas d’Annuler", async () => {
    phone();
    const wrapper = await mountDetail(offer({ score: 78, why: "x", summary_role: "x" }));
    await wrapper.find("[data-test=detail-more]").trigger("click");
    const sheet = wrapper.find("[data-test=offer-actions]");
    const titles = sheet.findAll(".offer-action").map((t) => t.text());
    expect(titles.slice(0, 3)).toEqual(["J’ai déjà postulé", "Signaler comme expirée", "Cette note ne me correspond pas"]);
    expect(titles).toContain("Partager");
    expect(titles.at(-1)).toBe("Écarter l’offre");
    expect(sheet.find(".offer-actions-end [data-test=offer-action-discard]").exists()).toBe(true);
    expect(sheet.find("[data-test=offer-actions-cancel]").exists()).toBe(false);
    expect(sheet.find("[data-test=sheet-close]").attributes("aria-label")).toBe("Fermer");
    expect(sheet.find("[data-test=sheet-handle]").exists()).toBe(false);
    expect(sheet.find(".sheet-title").text()).toBe(wrapper.props("offer").title);
    expect(titles).not.toContain("Plus tard");
    await sheet.find("[data-test=offer-action-score-correction-menu]").trigger("click");
    expect(wrapper.find("[data-test=score-correction-sheet] .score-correction-card.bare").exists()).toBe(true);
    vi.unstubAllGlobals();
  });

  it("la feuille « ⋯ » : « Remettre dans Nouvelles » seulement pour une offre gardée ou écartée (Kevin, 17.11)", async () => {
    phone();
    for (const [status, shown] of [["later", true], ["ignored", true], ["preparing", false], ["to_review", false]] as const) {
      const wrapper = await mountDetail(offer({ status }));
      await wrapper.find("[data-test=detail-more]").trigger("click");
      expect(wrapper.find("[data-test=offer-actions] [data-test=offer-action-back-to-review]").exists()).toBe(shown);
      wrapper.unmount();
    }
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

  it("le détail relié (maquette du 15 novembre, §18) : en-tête en carte avec la ligne de note, puis Candidature et L’offre en bref", async () => {
    desktop();
    const wrapper = await mountDetail(offer({ score: 60, snippet: "Kubernetes", employment_type: null, rate_min: null, rate_max: null }));
    // §18 : l'en-tête est la première carte : titre, entreprise, puis sous un filet « [libellé] · [note] sur 100 ».
    const head = wrapper.get("header[data-test=section-offer]");
    expect(head.classes()).toContain("oc-card");
    expect(head.get("[data-test=section-for-you]").text()).toContain("60 sur 100");
    expect(head.find(".score-ring").exists()).toBe(false);
    const cards = wrapper.findAll(".oc-card").map((card) => card.attributes("data-test"));
    expect(cards.slice(0, 3)).toEqual(["section-offer", "section-ad", "offer-brief"]);
    // La lecture de l'annonce complète est une ligne de la carte « Candidature » (§8, Offres, 3).
    expect(wrapper.find("[data-test=section-ad] [data-test=text-reading]").exists()).toBe(true);
    const brief = wrapper.get("[data-test=offer-brief]");
    const rows = brief.findAll("dl > div").map((row) => [row.find("dt").text(), row.find("dd").text()]);
    expect(rows.map((r) => r[0])).toEqual(["Lieu", "Contrat", "Taux d’activité", "Reçue"]);
    expect(rows[1]![1]).toBe("Non précisé");
    expect(brief.findAll("dd")[1]!.classes()).toContain("oc-missing");
    expect(rows[3]![1]).toMatch(/, par une alerte e-mail$/);
    const link = brief.get("[data-test=brief-link]");
    expect(link.attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(link.text()).toContain("Voir l’annonce sur Indeed");
    // Un seul lien visible vers l'annonce sur ordinateur aussi : celui de « L'offre en bref » (PR 25).
    expect(wrapper.findAll('a[href="https://ch.indeed.com/viewjob?jk=1"]')).toHaveLength(1);
    // Plus de puces dans l'en-tête, et jamais de puce qui dit qu'une information manque.
    expect(wrapper.find("[data-test=tag-contract]").exists()).toBe(false);
    // Les actions sont le pied de la carte « Candidature ».
    expect(wrapper.find("[data-test=section-ad] [data-test=triage] [data-test=prepare]").exists()).toBe(true);
  });

  it("la ligne de note avec « Voir la compatibilité », qui ouvre le panneau (§11)", async () => {
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

  it("une offre pas encore notée : « Pas encore notée » et « Donner l’annonce pour la noter » (§11)", async () => {
    desktop();
    const wrapper = await mountDetail(offer({ score: null, snippet: "Kubernetes" }));
    const line = wrapper.get("[data-test=section-for-you]");
    expect(line.text()).toContain("Pas encore notée");
    expect(line.find("[data-test=compat-open]").exists()).toBe(false);
    expect(line.get("[data-test=give-to-score]").attributes("aria-controls")).toBe("offer-give-zone");
  });

  it("K2 (planche OffreNonNotee, 18.11) : cercle pointillé, « Noter maintenant », temps et formule ; limite du mois dite", async () => {
    // Téléphone : la planche n'a pas de version ordinateur (question posée à Kevin).
    const wrapper = await mountDetail(offer({ score: null }));
    expect(wrapper.find("[data-test=match-unrated]").exists()).toBe(true);
    expect(wrapper.get("[data-test=match-sub]").text()).toBe("jobA1 n’a pas encore comparé cette offre à ton profil.");
    const block = wrapper.get("[data-test=score-now-block]");
    expect(block.get("[data-test=score-now]").text()).toContain("Noter maintenant");
    expect(block.text()).toContain("Environ 10 secondes · compte dans ta formule");
    POST.mockResolvedValue({ data: { score: 81, limit: null } });
    await block.get("[data-test=score-now]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/score-now", { params: { path: { offer_id: 4 } } });
    expect(wrapper.emitted("changed")).toBeTruthy();
    expect(wrapper.find("[data-test=score-now-error]").exists()).toBe(false);

    POST.mockResolvedValue({ data: { score: null, limit: "Les 30 offres notées du mois sont atteintes." } });
    await wrapper.get("[data-test=score-now]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-test=score-now-error]").text()).toBe("Les 30 offres notées du mois sont atteintes.");

    // Jamais sur une offre notée, écartée ou dont la note est impossible.
    expect((await mountDetail(offer({ score: 70 }))).find("[data-test=score-now-block]").exists()).toBe(false);
    expect((await mountDetail(offer({ score: null, status: "filtered_out" }))).find("[data-test=score-now-block]").exists()).toBe(false);
    expect((await mountDetail(offer({ score: null, score_final: "erreur" }))).find("[data-test=score-now-block]").exists()).toBe(false);
  });

  it("Kevin, 18.11 : sur ordinateur, les mêmes cartes dans le panneau (pas encore notée, expirée)", async () => {
    desktop();
    const unrated = await mountDetail(offer({ score: null }));
    expect(unrated.get("[data-test=match-sub]").text()).toBe("jobA1 n’a pas encore comparé cette offre à ton profil.");
    expect(unrated.get("[data-test=score-now-block] [data-test=score-now]").text()).toContain("Noter maintenant");
    const expired = await mountDetail(offer({ score: 70, expired_at: "2026-11-10T10:00:00Z", expiry_source: "manual" }));
    expect(expired.get("[data-test=expired]").classes()).toContain("oc-card");
    expect(expired.get("[data-test=expired] .expired-pill").text()).toBe("Offre expirée");
    expect(expired.get("[data-test=triage] [data-test=prepare]").text()).toBe("Écrire quand même");
  });

  it("A2 : note impossible, une ligne selon la cause ; « Réessayer » après un échec de l’IA (Kevin, 16.11)", async () => {
    desktop();
    const short = await mountDetail(offer({ score: null, score_final: "sans_texte" }));
    expect(short.get("[data-test=match-title]").text()).toBe("Note impossible");
    expect(short.get("[data-test=match-sub]").text()).toBe("L’annonce est trop courte pour être notée.");
    expect(short.find("[data-test=retry-score]").exists()).toBe(false);
    POST.mockResolvedValue({ data: { score: 70 } });
    const failed = await mountDetail(offer({ score: null, score_final: "erreur" }));
    expect(failed.get("[data-test=match-sub]").text()).toBe("La note n’a pas pu être calculée.");
    await failed.get("[data-test=retry-score]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/retry-score", { params: { path: { offer_id: 4 } } });
    expect(failed.emitted("changed")).toBeTruthy();
  });

  it("A2 : une offre écartée sans note n’affiche jamais « Pas encore notée »", async () => {
    desktop();
    const wrapper = await mountDetail(offer({ score: null, status: "filtered_out", filter_reasons: ["Mot exclu : stage"] }));
    expect(wrapper.get("[data-test=match-title]").text()).toBe("Écartée");
    expect(wrapper.text()).not.toContain("Pas encore notée");
  });

  it("§30 : « Écartée le 12 nov. », la pastille « Pas de note », « Remettre dans le tri » et plus de « Écarter »", async () => {
    desktop();
    const wrapper = await mountDetail(
      offer({ score: null, status: "ignored", set_aside_at: `${new Date().getFullYear()}-11-12T09:00:00Z` }),
    );
    expect(wrapper.get("[data-test=match-title]").text()).toBe("Écartée le 12 nov.");
    expect(wrapper.get("[data-test=aside-pill]").text()).toBe("Pas de note");
    expect(wrapper.find("[data-test=offer-discard]").exists()).toBe(false);
    await wrapper.get("[data-test=back-to-triage]").trigger("click");
    expect(wrapper.emitted("status")).toEqual([["to_review"]]);
    // Une autre année : l'année est dite.
    const old = await mountDetail(offer({ score: null, status: "filtered_out", set_aside_at: "2024-11-12T09:00:00Z" }));
    expect(old.get("[data-test=match-title]").text()).toBe("Écartée le 12 nov. 2024");
  });

  it("§30 sur téléphone : la carte de note finit par « Remettre dans le tri », « Préparer ma candidature » seul en bas", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px") || media.includes("599px"), addEventListener() {}, removeEventListener() {} }));
    const wrapper = await mountDetail(offer({ score: null, status: "filtered_out", set_aside_at: null }));
    expect(wrapper.get("[data-test=match-title]").text()).toBe("Écartée");
    expect(wrapper.get("[data-test=match-sub]").text()).toBe("Pas de note : jobA1 ne note pas les offres écartées.");
    expect(wrapper.find("[data-test=offer-discard]").exists()).toBe(false);
    expect(wrapper.find("[data-test=prepare]").exists()).toBe(true);
    await wrapper.get("[data-test=back-to-triage]").trigger("click");
    expect(wrapper.emitted("status")).toEqual([["to_review"]]);
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
