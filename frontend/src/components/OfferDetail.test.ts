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
  it("deux boutons, le reste dans ⋯, sans doublon de l'annonce d'origine (docs/45)", async () => {
    const wrapper = await mountDetail(offer());
    const triage = wrapper.find("[data-test=triage]");
    expect(triage.findAll("a")).toHaveLength(2);
    expect(wrapper.find("[data-test=apply]").attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(wrapper.find("[data-test=apply]").text()).toContain("Postuler sur Indeed");
    // « Voir sur Indeed » serait le même lien que « Postuler sur Indeed » : il n'apparaît pas.
    expect(wrapper.text()).not.toContain("Voir sur Indeed");
    expect(wrapper.find("[data-test=mark-applied]").exists()).toBe(false);
    await wrapper.find("[data-test=more]").trigger("click");
    for (const key of ["mark-applied", "later", "ignore", "flag-expired"]) {
      expect(wrapper.find(`[data-test=${key}]`).exists()).toBe(true);
    }
    // Chercher chez l'employeur est rangé dans la partie Entreprise (docs/74).
    expect(wrapper.find("[data-test=find-employer]").exists()).toBe(false);
  });

  it("cartes Pourquoi, Points forts, À savoir, puis Entreprise et Annonce repliées (planche « Fiche d'une offre »)", async () => {
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
    const titles = wrapper.findAll(".detail-card h3, .disclosure-title").map((h) => h.text());
    expect(titles).toEqual(["Pourquoi", "Points forts", "À savoir", "Entreprise", "Annonce"]);
    // Trois puces au plus, le mot clé en gras en tête.
    const points = wrapper.findAll("[data-test=strengths] li");
    expect(points).toHaveLength(3);
    expect(points[0]!.find("strong").text()).toBe("Kubernetes :");
    expect(points[0]!.text()).toBe("Kubernetes : plateforme de 40 services en production.");
    // L'entreprise et l'annonce, repliées, avec leur résumé (règles §3.4, 1.6.21).
    const rows = wrapper.findAll(".detail-disclosure > .disclosure-row");
    expect(rows.map((r) => r.attributes("aria-expanded"))).toEqual(["false", "false"]);
    expect(wrapper.find("[data-test=company-section] .disclosure-value").text()).toBe("Exemple SA");
    // « ← Offres » vient en premier, au-dessus du logo et du titre (règles §2).
    expect(wrapper.find("[data-test=offer-detail]").element.firstElementChild!.getAttribute("data-test")).toBe("back-detail");
    expect(wrapper.find("[data-test=score-note]").text()).toBe("Ton profil a changé depuis : note à refaire.");
    // À savoir : « libellé : valeur », seulement ce qui est connu ; plus de « 1 fois, depuis le… ».
    const labels = wrapper.findAll("[data-test=terms] dt").map((dt) => dt.text());
    expect(labels).toEqual(["Taux", "Télétravail", "Reçue", "Adresse"]);
    expect(wrapper.find("[data-test=term-remote] dd").text()).toBe("2 jours par semaine");
    expect(wrapper.find("[data-test=term-rate] dd").text()).toBe("80 à 100 %");
    const marks = wrapper.findAll("[data-test=facts] li").map((li) => li.find(".fact-mark [data-icon]").attributes("data-icon"));
    expect(marks).toEqual(["alert", "x-circle"]);
    expect(wrapper.text()).not.toMatch(/fois, depuis le/);
    // L'annonce chez l'employeur est le bouton ; celle d'Indeed, seule autre, s'affiche
    // directement, sans « ⋯ » pour une seule action (docs/76 §3).
    expect(wrapper.find("[data-test=ad-more]").exists()).toBe(false);
    expect(wrapper.find("[data-test=source-indeed]").text()).toContain("Voir sur Indeed");
    expect(wrapper.find("[data-test=section-facts] [data-test=address]").exists()).toBe(true);
    expect(wrapper.find("[data-test=description]").classes()).toContain("folded");
    await wrapper.find("[data-test=read-more]").trigger("click");
    expect(wrapper.find("[data-test=description]").classes()).not.toContain("folded");
    expect(wrapper.find("[data-test=read-more]").exists()).toBe(false);
  });

  it("annonce trouvée chez l'employeur : « Postuler chez l'employeur »", async () => {
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/jobs/2", employer_status: "found" }));
    const button = wrapper.find("[data-test=employer]");
    expect(button.attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(button.text()).toContain("Postuler chez l'employeur");
  });
});

describe("OfferDetail, partie Entreprise rangée (docs/74)", () => {
  it("l'adresse dans « À savoir », les actions dans le « ⋯ » de l'entreprise, « Adresse inconnue · Ajouter »", async () => {
    const known = await mountDetail(offer({ company_address: "Rue 1\n1201 Genève", company_address_source: "registry" }));
    expect(known.find("[data-test=address] dd").text()).toContain("Rue 1, 1201 Genève");
    expect(known.find("[data-test=add-address]").exists()).toBe(false);
    const section = known.find("[data-test=company-section]");
    await section.find("[data-test=company-more]").trigger("click");
    const labels = section.findAll("[role=menuitem]").map((item) => item.text());
    expect(labels).toEqual(["Modifier l'adresse", "Chercher l'adresse", "Chercher l'offre chez l'employeur", "Contacts"]);

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

describe("OfferDetail sur téléphone (planche « Tri et panneau de commande »)", () => {
  it("le panneau du bas : la note et pourquoi, « Préparer ma candidature », « Postuler » en lien", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px") || media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    const wrapper = await mountDetail(offer({ score: 78, why: "Kubernetes, Terraform et CI/CD : dans ton profil.", summary_role: "x" }));
    expect(wrapper.find("[data-test=triage]").exists()).toBe(false);
    const bar = wrapper.find("[data-test=action-bar]");
    expect(bar.find("[data-test=bar-score]").text()).toContain("Kubernetes, Terraform et CI/CD : dans ton profil.");
    expect(bar.find("[data-test=prepare]").text()).toBe("Préparer ma candidature");
    expect(bar.find("[data-test=apply]").classes()).toContain("link");
    // La note et sa phrase sont dans le panneau : sans niveau, la carte « Pourquoi » disparaît, et
    // « Cette note ne me correspond pas » passe dans « ⋯ », ouverte dans une feuille du bas.
    expect(wrapper.find("[data-test=section-for-you]").exists()).toBe(false);
    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=score-correction-menu]").trigger("click");
    const sheet = wrapper.find("[data-test=score-correction-sheet]");
    expect(sheet.find("[data-test=score-correction-open]").exists()).toBe(false);
    expect(sheet.find(".score-correction-card").exists()).toBe(true);
    // Avec un niveau, la carte reste, avec le niveau seul.
    const level = await mountDetail(offer({ score: 78, why: "x", summary_role: "x", level: "above", level_detail: "" }));
    expect(level.find("[data-test=section-for-you] [data-test=score-level]").exists()).toBe(true);
    expect(level.find("[data-test=section-for-you] [data-test=score-correction-open]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });

  it("une offre où j'ai postulé : pas de panneau", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("599px"), addEventListener() {}, removeEventListener() {} }));
    const wrapper = await mountDetail(offer({ status: "applied" }));
    expect(wrapper.find("[data-test=action-bar]").exists()).toBe(false);
    vi.unstubAllGlobals();
  });
});
