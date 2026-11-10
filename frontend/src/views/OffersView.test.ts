import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, onTestFinished, vi } from "vitest";
import { createMemoryHistory, createRouter, type Router } from "vue-router";

import { fromQuery, toQuery } from "../composables/useOfferFilters";
import { dayName } from "../format";
import OffersView from "./OffersView.vue";

const GET = vi.fn();
const PATCH = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
// Aucune note corrigée (docs/114) : sans cette réponse, la fiche recevait une page d'offres
// à la place de la correction et ScoreCorrection lisait un sens inexistant.
const NO_CORRECTION = "/api/offers/{offer_id}/score-correction";
vi.mock("../api/client", () => ({
  api: {
    PUT: (...args: unknown[]) => PUT(...args),
    GET: (...args: unknown[]) => (args[0] === NO_CORRECTION ? Promise.resolve({ data: null }) : GET(...args)),
    PATCH: (...args: unknown[]) => PATCH(...args),
    POST: (...args: unknown[]) => POST(...args),
  },
}));

const offer = (id: number, title: string, extra: Record<string, unknown> = {}) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne, VD",
  rate_min: 80,
  rate_max: 100,
  snippet: "Gérer l’infrastructure.",
  status: "to_review",
  first_seen_at: "2026-10-02T08:00:00Z",
  last_seen_at: "2026-10-02T08:00:00Z",
  seen_count: 1,
  links: [{ source: "jobup", url: `https://www.jobup.ch/fr/emplois/detail/${id}/` }],
  filter_reasons: [],
  ...extra,
});

function page(items: unknown[]) {
  return {
    data: {
      items,
      total: items.length,
      counts: { to_review: 5, pending: 6, filtered_out: 2, later: 0, in_progress: 0, expired: 3, all: 7 },
      facets: {
        sources: [
          { value: "indeed", count: 3 },
          { value: "jobup", count: 4 },
        ],
        cantons: [
          { value: "VD", count: 4 },
          { value: "GE", count: 1 },
        ],
      },
    },
  };
}

let router: Router;

function mockOffers(response: unknown): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/profile-chunks" ? { data: [{ id: 1, title: "Linux" }] } : response),
  );
}

async function mountAt(path: string) {
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/offres", component: OffersView },
      { path: "/aujourdhui/tri", name: "triage", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(OffersView, { global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } } });
  await flushPromises();
  return wrapper;
}

// « Filtrer » ouvre le panneau des filtres (1.6.55) : sans colonne, il est fermé à l'arrivée.
async function openFilters(wrapper: Awaited<ReturnType<typeof mountAt>>) {
  await wrapper.find("[data-test=filters-toggle]").trigger("click");
  await flushPromises();
}

function lastQuery(): Record<string, unknown> {
  const call = GET.mock.calls.filter((c) => c[0] === "/api/offers").at(-1);
  return (call?.[1] as { params: { query: Record<string, unknown> } }).params.query;
}

beforeEach(() =>
  GET.mockImplementation((path: string) =>
    Promise.resolve(
      path === "/api/profile-chunks"
        ? { data: [{ id: 1, title: "Linux" }] }
        : page([offer(1, "Ingénieur système")]),
    ),
  ),
);
afterEach(() => {
  GET.mockReset();
  vi.useRealTimers();
});

describe("filtres dans l’adresse", () => {
  it("lit et écrit les filtres", () => {
    const filters = fromQuery({ canton: ["vd", "GE"], site: "jobup", taux: "80", externe: "1", statut: "all" });
    expect(filters).toMatchObject({
      view: "all",
      cantons: ["VD", "GE"],
      sources: ["jobup"],
      minRate: 80,
      externalOnly: true,
    });
    expect(toQuery(filters)).toEqual({
      statut: "all",
      canton: ["VD", "GE"],
      site: ["jobup"],
      taux: "80",
      externe: "1",
    });
    expect(fromQuery({ taux: "abc", site: "Monster!", statut: "?" })).toMatchObject({
      minRate: null,
      sources: [],
      view: "pending",
    });
  });
});

describe("OffersView", () => {
  it("un compte neuf, sans filtre : pourquoi c’est vide, et quoi faire (docs/128 §3)", async () => {
    const none = { to_review: 0, filtered_out: 0, later: 0, in_progress: 0, expired: 0, all: 0 };
    mockOffers({ data: { ...page([]).data, counts: none } });
    const wrapper = await mountAt("/offres");
    const empty = wrapper.find("[data-test=offers-none-yet]");
    expect(empty.text()).toContain("Tes premières offres arrivent après la prochaine collecte.");
    expect(empty.find("[data-scene=aucune-offre]").exists()).toBe(true);
    // « Ajouter une offre » seulement dans l'écran vide, et la conclusion en une phrase (1.6.18).
    expect(wrapper.find("[data-test=manual-open]").exists()).toBe(false);
    expect(wrapper.find("[data-test=offers-none-add]").exists()).toBe(true);
    expect(wrapper.find("[data-test=offers-sentence]").text()).toBe("Aucune offre à traiter.");
    expect(empty.find("a").attributes("href")).toBe("/candidatures/alertes");
    expect(wrapper.find("[data-test=offers-empty]").exists()).toBe(false);
    // Des filtres : c'est « rien ne correspond », pas un compte neuf.
    const filtered = await mountAt("/offres?canton=VD");
    expect(filtered.find("[data-test=offers-none-yet]").exists()).toBe(false);
    expect(filtered.find("[data-test=offers-empty]").exists()).toBe(true);
    // Aucun résultat avec des filtres (règles §4) : une ligne grise et le lien « Effacer les filtres ».
    expect(filtered.find("[data-test=offers-empty]").text()).toContain("Aucune offre avec ces filtres.");
    expect(filtered.find("[data-test=offers-reset]").classes()).toContain("link");
  });

  it("ordinateur large, aucune offre avec ces filtres (§2.7 du 9 novembre) : « Faire une candidature spontanée » ouvre « Ajouter »", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("1024px"), addEventListener() {}, removeEventListener() {} }));
    mockOffers(page([]));
    const filtered = await mountAt("/offres?canton=VD");
    // Plus de lien « Postuler spontanément » en bas de liste sur ordinateur.
    expect(filtered.find(".offers-spontaneous").exists()).toBe(false);
    const link = filtered.get("[data-test=offers-empty] [data-test=empty-spontaneous]");
    expect(filtered.find(".offers-empty-spontaneous p").text()).toBe("Tu vises une entreprise précise, même sans offre ?");
    await link.trigger("click");
    expect(filtered.get("[data-test=add-sheet] [data-test=add-tab-spontaneous]").attributes("aria-checked")).toBe("true");
    vi.unstubAllGlobals();
  });

  it("la conclusion en une phrase, selon le statut regardé (règles §3.2, 1.6.18)", async () => {
    mockOffers(page([offer(1, "Une"), offer(2, "Deux")]));
    const wrapper = await mountAt("/offres");
    expect(wrapper.find("[data-test=offers-sentence]").text()).toBe("2 offres à traiter.");
    expect(wrapper.find("[data-test=offers-sentence] strong").text()).toBe("2 offres");
    // La phrase décrit la liste affichée, sans le nombre de tout « À traiter » (2026-11-03).
    const inProgress = await mountAt("/offres?statut=in_progress");
    expect(inProgress.find("[data-test=offers-sentence]").text()).toBe("2 offres en cours.");
    const searched = await mountAt("/offres?q=devops");
    expect(searched.find("[data-test=offers-sentence]").text()).toBe("2 offres à traiter avec ces filtres.");
    const mixed = await mountAt("/offres?ecartees=montrer");
    expect(mixed.find("[data-test=offers-sentence]").text()).toBe("2 offres affichées avec ces filtres.");
    // Un seul bouton « + Ajouter » (§2.6 du 9 novembre) : un panneau à deux onglets, « Une offre » d'abord.
    await wrapper.find("[data-test=add-open]").trigger("click");
    const sheet = wrapper.find("[data-test=add-sheet]");
    expect(sheet.find("[data-test=add-tab-offer]").attributes("aria-checked")).toBe("true");
    expect(sheet.text()).toContain("Colle le lien ou le texte de l’annonce.");
    await sheet.find("[data-test=add-tab-spontaneous]").trigger("click");
    expect(wrapper.find("[data-test=add-sheet] [data-test=add-tab-spontaneous]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=add-sheet] [data-test=composer-input]").exists()).toBe(false);
    mockOffers(page([offer(3, "Trois")]));
    const dropped = await mountAt("/offres?statut=filtered_out");
    // Dans une autre vue, la phrase redit ce que compte la pastille de l'onglet (1.6.27).
    expect(dropped.find("[data-test=offers-sentence]").text().replace(/\s+/g, " ")).toMatch(/^1 offre écartée( · \d+ à traiter)?\.$/);
  });

  it("transmet les filtres de l’adresse à l’API", async () => {
    await mountAt("/offres?canton=VD&taux=80&site=jobup&externe=1&q=linux");
    expect(lastQuery()).toMatchObject({
      view: "pending",
      cantons: ["VD"],
      min_rate: 80,
      sources: ["jobup"],
      external_only: true,
      q: "linux",
    });
  });

  // Le panneau de la maquette CandidaturesOrdinateur (7.11.2026) : des pastilles aria-pressed, appliquées tout de suite.
  it("un clic sur un filtre met à jour l’adresse et recharge", async () => {
    const wrapper = await mountAt("/offres");
    await openFilters(wrapper);
    expect(wrapper.find("[data-test=pop-view-pending]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=pop-view-pending]").text()).toMatch(/^À traiter · \d+$/);
    await wrapper.find("[data-test=pop-score-75]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ note: "75" });
    expect(lastQuery()).toMatchObject({ min_score: 75 });
    expect(wrapper.find("[data-test=pop-score-75]").attributes("aria-pressed")).toBe("true");
    await wrapper.find("[data-test=pop-rate-80]").trigger("click");
    await wrapper.find("[data-test=pop-view-to_review]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ note: "75", taux: "80", statut: "to_review" });
    expect(wrapper.find("[data-test=filters-reset]").text()).toBe("Tout effacer");
    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ statut: "to_review" });
  });

  it("le panneau : un seul conteneur, le milieu défile, le pied reste", async () => {
    const wrapper = await mountAt("/offres");
    await openFilters(wrapper);
    const dialog = wrapper.find("[data-test=filters-dialog]");
    expect(dialog.findAll(".filter-panel-group > span").map((g) => g.text())).toEqual(["Statut", "Trier", "Correspondance minimale", "Taux minimum"]);
    expect(dialog.findAll("[aria-pressed]").length).toBe(14);
    expect(dialog.find(".filter-panel-body [data-test=filters-done]").exists()).toBe(false);
    expect(dialog.find(".filter-panel-foot [data-test=filters-done]").exists()).toBe(true);
    await wrapper.find("[data-test=pop-filtered-out]").trigger("change");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ ecartees: "montrer" });
  });

  it("la recherche attend la fin de la frappe", async () => {
    vi.useFakeTimers();
    const wrapper = await mountAt("/offres");
    const calls = GET.mock.calls.filter((c) => c[0] === "/api/offers").length;
    await wrapper.find("[data-test=search]").setValue("dev");
    await wrapper.find("[data-test=search]").setValue("devops");
    expect(GET.mock.calls.filter((c) => c[0] === "/api/offers").length).toBe(calls);
    await vi.advanceTimersByTimeAsync(350);
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ q: "devops" });
    expect(lastQuery()).toMatchObject({ q: "devops" });
  });

  it("détail : candidature, raisons, texte complet, fermeture", async () => {
    mockOffers(
      page([
        offer(7, "Ingénieur VMware", {
          apply_url: "https://www.aplitrak.com/?adid=x",
          apply_kind: "external",
          description: "Notre client recherche un ingénieur.",
          employment_type: "Temporaire",
        }),
        offer(8, "Stage DevOps", { status: "filtered_out", filter_reasons: ["Type : stage (« stage »)"] }),
      ]),
    );
    const wrapper = await mountAt("/offres");
    const cards = wrapper.findAll("[data-test=offer]");
    // Une ligne (docs/73 §4) : le site et « chez l'employeur » sont dans le panneau.
    expect(cards[0]?.text()).not.toContain("chez l’employeur");
    // Pas encore notée : pas d'anneau, le texte, et la raison au survol (docs/76 §3).
    expect(cards[0]?.find("[data-test=score]").attributes("title")).toContain("à noter");
    expect(cards[0]?.findAll("[data-test=offer-chip]").map((c) => c.text())).toEqual(["80–100 %", "Temporaire"]);
    expect(cards[1]?.find("[data-test=offer-chip]").text()).toBe("Type : stage (« stage »)");
    expect(cards[1]?.find("[data-test=offer-chip]").classes()).toContain("warn");

    await cards[0]?.trigger("click");
    const apply = wrapper.find("[data-test=apply]");
    expect(apply.text()).toContain("Postuler chez l’employeur");
    expect(apply.attributes("rel")).toBe("noopener noreferrer");
    expect(wrapper.find("[data-test=description]").text()).toBe("Notre client recherche un ingénieur.");
    expect(wrapper.text()).toContain("Temporaire");

    await wrapper.find("[data-test=close-detail]").trigger("click");
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);

    await cards[1]?.trigger("click");
    expect(wrapper.find("[data-test=facts] .no").text()).toContain("Type : stage");
  });
});

describe("note et résumé", () => {
  it("carte avec note et résumé, détail avec points forts", async () => {
    mockOffers(
      page([
        offer(9, "Ingénieur système", {
          score: 82,
          summary_role: "Exploiter des serveurs Linux",
          summary_asks: "5 ans Linux, Ansible",
          summary_offers: "80-100 %, salaire non précisé",
          strengths: [{ text: "Linux solide", chunk_ids: [1] }],
          gaps: [{ text: "Pas d’Ansible", chunk_ids: [] }],
          scored_at: "2026-10-05T08:00:00Z",
          // Texte complet lu : la note n'est pas provisoire, ses manques s'affichent.
          description: "Texte complet de l’annonce.",
        }),
        offer(10, "Pas notée"),
      ]),
    );
    const wrapper = await mountAt("/offres?tri=score&note=70");
    expect(lastQuery()).toMatchObject({ sort: "score", min_score: 70 });
    const [scored, unscored] = wrapper.findAll("[data-test=offer]");
    // L'anneau avec son chiffre, le mot dessous (2026-11-05, Kevin).
    expect(scored?.find("[data-test=score]").text()).toBe("82Proche");
    expect(scored?.find("[data-test=score]").classes()).toContain("close");
    expect(scored?.find("[data-test=score]").attributes("aria-label")).toBe("Proche : 82 sur 100");
    expect(scored?.find(".score-ring-arc").attributes("stroke-dasharray")).toBe("216.39 263.89");
    expect(scored?.find(".score-line").exists()).toBe(false);
    // Le résumé est dans le panneau ; hors du tri par jour, la date revient dans l'offre.
    expect(scored?.find("[data-test=summary]").exists()).toBe(false);
    expect(scored?.findAll("[data-test=offer-chip]").at(-1)?.text()).toMatch(/^Reçue (le )?\d{1,2} \S+$|^Reçue (aujourd’hui|hier)$/);
    expect(wrapper.findAll("[data-test=offer-day]")).toHaveLength(0);
    expect(unscored?.find("[data-test=score]").classes()).toContain("score-pending");

    await scored?.trigger("click");
    expect(wrapper.find("[data-test=match-title]").text()).toBe("Proche de ton profil");
    expect(wrapper.find("[data-test=match-sub]").text()).toBe("Selon ton profil et tes préférences");
    expect(wrapper.find("[data-test=match-sub]").text()).not.toContain("82/100");

    // Le bloc d'où vient le point fort, au survol (docs/131 §B.7).
    const strengths = wrapper.find("[data-test=strengths]");
    // Plus de soulignement pointillé ni de bloc au survol (planche « Fiche d'une offre »).
    expect(strengths.text()).toBe("Linux solide");
    expect(strengths.findComponent({ name: "HoverNote" }).exists()).toBe(false);
    expect(wrapper.find("[data-test=gaps]").text()).toContain("Pas d’Ansible");
  });
});

describe("tri et candidature", () => {
  it("ouvrir une offre : l’adresse la suit, le focus passe à son titre, « Retour » la referme", async () => {
    const wrapper = await mountAt("/offres");
    document.body.appendChild(wrapper.element);
    await wrapper.find("[data-test=offer]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.offre).toBe("1");
    expect(document.activeElement?.getAttribute("data-test")).toBe("offer-detail-title");
    // La carte ouverte (maquette CandidaturesOrdinateur) : aria-current="true", un lien vers ?offre=.
    expect(wrapper.find("[data-test=offer]").attributes("aria-current")).toBe("true");
    expect(wrapper.find("[data-test=offer]").attributes("href")).toBe("/offres?offre=1");
    router.back();
    await flushPromises();
    await new Promise((r) => setTimeout(r, 0));
    await flushPromises();
    expect(router.currentRoute.value.query.offre).toBeUndefined();
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("« Plus tard » change le statut et ferme le détail", async () => {
    PATCH.mockResolvedValue({ data: { id: 1, status: "later" } });
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=later]").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/status", {
      params: { path: { offer_id: 1 } },
      body: { status: "later" },
    });
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);
    // Le message propose d'annuler (docs/60 §3) : l'offre revient à son statut d'avant.
    expect(wrapper.text()).toContain("Passée en Plus tard.");
    await wrapper.find("[data-test=undo-status]").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/status", {
      params: { path: { offer_id: 1 } },
      body: { status: "to_review" },
    });
  });

  it("« Marquer comme envoyée » pré-remplit puis enregistre la candidature", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offers/{offer_id}/application-prefill"
          ? {
              data: {
                offer_id: 1,
                sent_at: "2026-10-05",
                method: "electronique",
                assigned_by_orp: false,
                company: "Acme SA",
                job_title: "Ingénieur système",
                location: "Lausanne, VD",
                rate_text: "plein temps ou temps partiel (80-100 %)",
              },
            }
          : path === "/api/profile-chunks"
            ? { data: [] }
            : page([offer(1, "Ingénieur système")]),
      ),
    );
    POST.mockResolvedValue({ data: { id: 9, company: "Acme SA", job_title: "Ingénieur système", orp_month: "2026-10", follow_up_on: "2026-10-16" } });
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=mark-applied]").trigger("click");
    await flushPromises();
    await wrapper.find("form.application-form").trigger("submit");
    await flushPromises();
    const [path, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications");
    expect(opts.body).toMatchObject({ offer_id: 1, company: "Acme SA", rate_text: "plein temps ou temps partiel (80-100 %)" });
    // « Candidature envoyée. » à la place de la page (docs/141, 8), avec la relance prévue.
    const done = wrapper.find("[data-test=sent-moment]");
    expect(done.find("h1").text()).toBe("Candidature envoyée.");
    expect(done.text()).toContain("Ingénieur système chez Acme SA.");
    expect(done.find("[data-test=sent-follow-up]").text()).toMatch(/^Relance prévue le 16 octobre( 2026)? si pas de réponse\.$/);
    expect(done.find("[data-test=cancel-applied]").exists()).toBe(false);
    // « Préparer la prochaine » referme l'écran : la liste revient.
    await done.find("[data-test=next-offer]").trigger("click");
    expect(wrapper.find("[data-test=sent-moment]").exists()).toBe(false);
  });
});

describe("offres expirées", () => {
  it("onglet Expirées et bandeau dans le détail", async () => {
    mockOffers(
      page([offer(4, "Ingénieur cloud", { expired_at: "2026-10-04T08:00:00Z", expiry_source: "age" })]),
    );
    const wrapper = await mountAt("/offres?statut=expired");
    expect(lastQuery().view).toBe("expired");
    await wrapper.find("[data-test=offer]").trigger("click");
    expect(wrapper.find("[data-test=expired]").text()).toContain("Probablement expirée");
  });
});

describe("expiration signalée", () => {
  it("signaler comme expirée puis « Pas expirée »", async () => {
    PATCH.mockResolvedValue({ data: { id: 1 } });
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=flag-expired]").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/expiry", {
      params: { path: { offer_id: 1 } },
      body: { expired: true },
    });
    expect(wrapper.text()).toContain("Offre signalée comme expirée.");

    mockOffers(page([offer(5, "Ingénieur cloud", { expired_at: "2026-10-04T08:00:00Z", expiry_source: "manual" })]));
    const expired = await mountAt("/offres?statut=expired");
    await expired.find("[data-test=offer]").trigger("click");
    expect(expired.find("[data-test=expired]").text()).toContain("Signalée expirée par toi");
    await expired.find("[data-test=more]").trigger("click");
    await expired.find("[data-test=not-expired]").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/expiry", {
      params: { path: { offer_id: 5 } },
      body: { expired: false },
    });
  });
});

describe("détail allégé et adresse", () => {
  it("pastille de statut, menu « ⋯ » et adresse modifiable", async () => {
    PATCH.mockResolvedValue({ data: { id: 1 } });
    mockOffers(
      page([
        offer(1, "Ingénieur système", {
          status: "later",
          company_address: "Chemin de l’Exemple 10\n1206 Genève",
          company_address_source: "page",
        }),
      ]),
    );
    const wrapper = await mountAt("/offres?statut=later");
    await wrapper.find("[data-test=offer]").trigger("click");
    expect(wrapper.find("[data-test=status-pill]").text()).toBe("Plus tard");
    expect(wrapper.find("[data-test=later]").exists()).toBe(false);
    expect(wrapper.find("[data-test=address]").text()).toContain("Chemin de l’Exemple 10, 1206 Genève");
    expect(wrapper.find("[data-test=address]").text()).toContain("annonce");

    await wrapper.find("[data-test=more]").trigger("click");
    expect(wrapper.find("[data-test=back-to-review]").exists()).toBe(true);

    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=edit-address]").trigger("click");
    await wrapper.find("[data-test=address-input]").setValue("Rue du Port 2\n1201 Genève");
    await wrapper.find("[data-test=save-address]").trigger("submit");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/address", {
      params: { path: { offer_id: 1 } },
      body: { address: "Rue du Port 2\n1201 Genève" },
    });
  });
});

describe("adresse par le registre IDE", () => {
  it("propose les entreprises possibles puis enregistre le choix", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(path === "/api/profile-chunks" ? { data: [] } : page([offer(1, "Ingénieur système")])),
    );
    // La recherche est une écriture (docs/78 §2), le choix aussi.
    POST.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offers/{offer_id}/address-candidates"
          ? {
              data: {
                chosen_uid: null,
                candidates: [
                  { uid: "CHE1", name: "Exemple SA", address: "Rue 1\n1206 Genève", canton: "GE" },
                  { uid: "CHE2", name: "Exemple Sàrl", address: "Rue 2\n1206 Genève", canton: "GE" },
                ],
              },
            }
          : { data: { company_address: "Rue 2\n1206 Genève", company_address_source: "registry" } },
      ),
    );
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=search-registry]").trigger("click");
    await flushPromises();
    const choices = wrapper.findAll("[data-test=choose-registry]");
    expect(choices).toHaveLength(2);
    expect(wrapper.find("[data-test=registry]").text()).toContain("Rue 2, 1206 Genève");
    await choices[1]!.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/address-candidates/choose", {
      params: { path: { offer_id: 1 } },
      body: { uid: "CHE2" },
    });
    expect(wrapper.findAll("[data-test=choose-registry]")).toHaveLength(0);
  });
});

describe("étiquettes en mots-clés", () => {
  // Maquette du 7.11.2026 : rien d'autre que les puces dans la carte ; ce qui manque est dans la fiche.
  it("ni mots-clés ni « Il te manque » sur la carte (docs/73 §4, maquette du 7.11)", async () => {
    mockOffers(
      page([
        offer(1, "Ingénieur DevOps", {
          score: 72,
          summary_role: "Exploiter la plateforme",
          keywords_role: ["DevOps", "AWS"],
          keywords_asks: [
            { text: "Kubernetes", covered: true },
            { text: "allemand B2", covered: false },
          ],
          keywords_offers: ["80-100 %", "CDI"],
        }),
        offer(2, "Ancienne note", { score: 60, summary_role: "Phrase complète du poste", summary_asks: "x", summary_offers: "y" }),
      ]),
    );
    const wrapper = await mountAt("/offres");
    const cards = wrapper.findAll("[data-test=offer]");
    expect(cards[0]!.find("[data-test=keywords]").exists()).toBe(false);
    expect(cards[0]!.text()).not.toContain("Il te manque");
    expect(cards[0]!.text()).not.toContain("80-100 %");
  });
});

describe("tri « Dernière action »", () => {
  it("devient le tri de l’onglet En cours, et disparaît en le quittant", async () => {
    const wrapper = await mountAt("/offres");
    expect(wrapper.text()).not.toContain("Dernière action");
    await openFilters(wrapper);
    await wrapper.find("[data-test=pop-view-in_progress]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toMatchObject({ statut: "in_progress", tri: "activity" });
    expect(lastQuery().sort).toBe("activity");
    expect(wrapper.find("[data-test=pop-sort-activity]").attributes("aria-pressed")).toBe("true");

    await wrapper.find("[data-test=pop-view-to_review]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.tri).toBeUndefined();
  });
});

describe("Offres, revue des pages (docs/43)", () => {
  it("une ligne par jour, les offres sans leur date ; « + Ajouter » dans la barre d’outils", async () => {
    // Une horloge figée en milieu de journée : les jours sont rangés à l'heure de Zurich, et le soir du changement
    // d'heure (ou une machine en UTC), « 24 h plus tôt » pouvait encore être aujourd'hui.
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-14T10:00:00Z"));
    onTestFinished(() => {
      vi.useRealTimers();
    });
    const ago = (days: number) => new Date(Date.now() - days * 86_400_000).toISOString();
    mockOffers(
      page([
        offer(1, "Aujourd’hui", { first_seen_at: ago(0) }),
        offer(2, "Hier", { first_seen_at: ago(1) }),
        offer(3, "Hier aussi", { first_seen_at: ago(1) }),
        offer(4, "Ancienne", { first_seen_at: ago(20) }),
      ]),
    );
    const wrapper = await mountAt("/offres");
    const days = wrapper.findAll("[data-test=offer-day]");
    expect(days.map((h) => h.find(".offer-day-name").text())).toEqual(["Aujourd’hui", "Hier", dayName(ago(20))]);
    expect(days.map((h) => h.find(".offer-day-count").text())).toEqual(["1 offre", "2 offres", "1 offre"]);
    expect(wrapper.findAll(".offer-line-sub").every((sub) => !/ · \d{1,2} \S+$/.test(sub.text()))).toBe(true);
    // « + Ajouter » dans la barre d'outils : il ouvre le panneau à deux onglets (§2.6 du 9 novembre).
    const add = wrapper.find("[data-test=offers-toolbar] [data-test=add-open]");
    expect(add.text()).toBe("Ajouter");
    await add.trigger("click");
    expect(wrapper.findAll("[data-test=add-sheet] [role=radio]").map((i) => i.text())).toEqual(["Une offre", "Candidature spontanée"]);
    // Aucun filtre actif : ni pastille, ni nombre sur « Filtrer », ni « Tout effacer ».
    expect(wrapper.find("[data-test=filter-chips]").exists()).toBe(false);
    expect(wrapper.find("[data-test=filters-count]").exists()).toBe(false);
    await openFilters(wrapper);
    expect(wrapper.find("[data-test=reset]").exists()).toBe(false);
  });
});

describe("Offres, offre ouverte par un lien (docs/43, complément)", () => {
  it("posée en tête sans intertitre, hors des groupes", async () => {
    const ago = (days: number) => new Date(Date.now() - days * 86_400_000).toISOString();
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offers/{offer_id}"
          ? { data: offer(9, "En préparation", { status: "preparing", first_seen_at: ago(40) }) }
          : path === "/api/profile-chunks"
            ? { data: [] }
            : page([offer(1, "Récente", { first_seen_at: ago(2) }), offer(2, "Ancienne", { first_seen_at: ago(20) })]),
      ),
    );
    const wrapper = await mountAt("/offres?offre=9");
    const first = wrapper.findAll("[data-test=offer]")[0]!;
    expect(first.text()).toContain("En préparation");
    // Sans ligne de jour au-dessus, elle garde sa date.
    expect(first.findAll("[data-test=offer-chip]").at(-1)?.text()).toMatch(/^Reçue (le )?\d{1,2} \S+/);
    expect(wrapper.findAll("[data-test=offer-day] .offer-day-name").map((h) => h.text())).toEqual([
      dayName(ago(2)),
      dayName(ago(20)),
    ]);
  });
});

describe("Offres, ajouter une offre (docs/111)", () => {
  it("« Partager vers jobA1 » ouvre le formulaire, le lien sorti du texte partagé", async () => {
    mockOffers(page([offer(1, "Une")]));
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offers/manual"
          ? { data: { trade: "Menuisier", added_today: 0, daily_limit: 20 } }
          : path === "/api/profile-chunks"
            ? { data: [] }
            : page([offer(1, "Une")]),
      ),
    );
    const wrapper = await mountAt("/offres?ajouter=1&text=" + encodeURIComponent("Menuisier CFC https://bois.ch/emplois/1"));
    expect(wrapper.find("[data-test=offers-toolbar] [data-test=add-open]").exists()).toBe(true);
    const input = wrapper.find("[data-test=composer-input]").element as HTMLTextAreaElement;
    expect(input.value).toBe("https://bois.ch/emplois/1");
    expect(router.currentRoute.value.query.ajouter).toBeUndefined();
  });

  // L'offre ajoutée n'est pas dans la page chargée (pas encore notée, ou écartée) : elle est posée en
  // tête et reste ouverte. Avant, ?offre= dans l'adresse relançait le chargement de la liste, qui
  // l'effaçait aussitôt et refermait sa fiche.
  it("l’offre ajoutée s’ouvre et reste ouverte", async () => {
    // La liste répond après l'offre seule, comme sur le serveur.
    const later = <T,>(value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), 20));
    GET.mockImplementation((path: string) =>
      path === "/api/offers/manual"
        ? Promise.resolve({ data: { trade: "Menuisier", added_today: 0, daily_limit: 20 } })
        : path === "/api/offers/{offer_id}"
          ? Promise.resolve({ data: offer(9, "Menuisier CFC", { added_by_you: true, links: [] }) })
          : path === "/api/profile-chunks"
            ? Promise.resolve({ data: [] })
            : later(page([offer(1, "Une")])),
    );
    const wrapper = await mountAt("/offres?ajouter=1");
    await new Promise((resolve) => setTimeout(resolve, 50));
    await flushPromises();
    const listLoads = () => GET.mock.calls.filter((c) => c[0] === "/api/offers").length;
    const before = listLoads();
    wrapper.findComponent({ name: "ManualOfferForm" }).vm.$emit("added", { id: 9, existing: false, status: "to_review", reasons: [] });
    await new Promise((resolve) => setTimeout(resolve, 150));
    await flushPromises();
    expect(router.currentRoute.value.query.offre).toBe("9");
    expect(wrapper.find("[data-test=offer-detail-title]").text()).toContain("Menuisier CFC");
    expect(wrapper.findAll("[data-test=offer]")[0]!.text()).toContain("Menuisier CFC");
    // Une seule relecture de la liste, celle qui suit l'ajout.
    expect(listLoads() - before).toBe(1);
  });

  it("l’étiquette « Ajoutée par toi » sur la carte", async () => {
    mockOffers(page([offer(1, "Une", { added_by_you: true, links: [] })]));
    const wrapper = await mountAt("/offres");
    const chip = wrapper.findAll("[data-test=offer-chip]").find((c) => c.text() === "Ajoutée par toi");
    expect(chip?.classes()).toContain("blue");
  });
});

describe("Offres, sans bande d’action (1.6.53)", () => {
  it("des offres à examiner : pas de bande, la liste est déjà la tâche", async () => {
    const now = new Date().toISOString();
    mockOffers(page([offer(1, "Une", { score: 90, first_seen_at: now }), offer(2, "Deux", { score: 60, first_seen_at: now })]));
    const wrapper = await mountAt("/offres");
    // Le nombre est dans l'onglet et dans la conclusion ; la bande ne le répète pas (règles §3).
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Commencer le tri");
  });

  it("tout est examiné : pas de bande, « Tout est examiné » sans bouton, « Aucune offre à traiter. »", async () => {
    const reviewed = { to_review: 0, pending: 0, filtered_out: 2, later: 0, in_progress: 3, expired: 1, all: 6 };
    mockOffers({ data: { ...page([]).data, counts: reviewed } });
    const wrapper = await mountAt("/offres");
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    const done = wrapper.find("[data-test=offers-all-reviewed]");
    expect(done.find(".face-state-title").text()).toBe("Tout est examiné");
    expect(done.text()).toContain("Les nouvelles arrivent chaque matin.");
    expect(done.find("button, a").exists()).toBe(false);
    expect(wrapper.find("[data-test=offers-sentence]").text()).toBe("Aucune offre à traiter.");
  });
});

describe("Offres, barre d’outils (1.6.55)", () => {
  it("la recherche dans la barre, « Filtrer » ouvre le panneau, « Afficher N offres » le referme", async () => {
    mockOffers(page([offer(1, "Une"), offer(2, "Deux")]));
    const wrapper = await mountAt("/offres");
    const bar = wrapper.find("[data-test=offers-toolbar]");
    // Ordinateur : la recherche est dans la barre, pas dans le panneau.
    expect(bar.find("[data-test=search]").exists()).toBe(true);
    expect(wrapper.find("[data-test=filters-dialog]").exists()).toBe(false);
    const toggle = wrapper.find("[data-test=filters-toggle]");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    await openFilters(wrapper);
    expect(toggle.attributes("aria-expanded")).toBe("true");
    const dialog = wrapper.find("[data-test=filters-dialog]");
    expect(dialog.find("h2").text()).toBe("Filtres");
    expect(dialog.find("[data-test=search]").exists()).toBe(false);
    expect(wrapper.find("[data-test=filters-done]").text()).toBe("Afficher 2 offres");
    await wrapper.find("[data-test=filters-done]").trigger("click");
    expect(wrapper.find("[data-test=filters-dialog]").exists()).toBe(false);
    // Un clic hors du panneau le referme aussi.
    await openFilters(wrapper);
    document.body.dispatchEvent(new Event("pointerdown", { bubbles: true }));
    await flushPromises();
    expect(wrapper.find("[data-test=filters-dialog]").exists()).toBe(false);
  });

  it("les filtres actifs en pastilles : le nombre sur « Filtrer », la croix retire, « Tout effacer » vide", async () => {
    const wrapper = await mountAt("/offres?note=70&canton=VD&canton=GE&externe=1&q=dev");
    const chips = wrapper.findAll("[data-test=filter-chips] li").map((c) => c.text());
    // La recherche n'a pas de pastille : son champ est dans la barre.
    expect(chips).toEqual(["Note minimale : Proche et plus", "Canton : VD", "Canton : GE", "Chez l’employeur"]);
    expect(wrapper.find("[data-test=filters-count]").text()).toBe("4");
    expect(wrapper.find("[data-test=filters-toggle]").attributes("aria-label")).toBe("Filtrer, 4 filtres actifs");
    await wrapper.find("[data-test=chip-remove-canton-VD]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ note: "70", canton: ["GE"], externe: "1", q: "dev" });
    await wrapper.find("[data-test=chips-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});
    expect(wrapper.find("[data-test=filter-chips]").exists()).toBe(false);
  });
});

describe("Offres, illustrations (planche « Illustrations »)", () => {
  it("rien en préparation : « Rien à préparer pour l’instant », vers le tri", async () => {
    mockOffers(page([]));
    const wrapper = await mountAt("/offres?statut=in_progress");
    const empty = wrapper.find("[data-test=offers-nothing-to-prepare]");
    expect(empty.find(".face-state-title").text()).toBe("Rien à préparer pour l’instant");
    expect(empty.find(".illu").exists()).toBe(true);
    expect(empty.find("a").attributes("href")).toBe("/aujourdhui/tri");
  });

  it("panne de réseau : l’écran « Pas de connexion » au lieu du message d’erreur", async () => {
    GET.mockImplementation((path: string) =>
      path === "/api/offers" ? Promise.reject(new TypeError("Failed to fetch")) : Promise.resolve({ data: [] }),
    );
    const wrapper = await mountAt("/offres");
    expect(wrapper.find("[data-test=network-error]").exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Impossible de charger les offres.");
  });
});

describe("À traiter (docs/139 étape 5b, C2 et C8)", () => {
  it("en préparation d’abord, sous son titre ; « Plus tard » et les faits en puces", async () => {
    const now = new Date().toISOString();
    mockOffers(
      page([
        offer(1, "Lettre en cours", { status: "preparing", first_seen_at: now }),
        offer(2, "Gardée", { status: "later", first_seen_at: now, employment_type: "CDI" }),
        offer(3, "Nouvelle", { first_seen_at: now }),
      ]),
    );
    const wrapper = await mountAt("/offres");
    expect(lastQuery().view).toBe("pending");
    const titles = wrapper.findAll("[data-test=offer-day] .offer-day-name").map((h) => h.text());
    expect(titles).toEqual(["En préparation", "Aujourd’hui"]);
    const cards = wrapper.findAll("[data-test=offer]");
    expect(cards[0]!.text()).not.toContain("En préparation");
    expect(cards[1]!.findAll("[data-test=offer-chip]").map((s) => s.text())).toEqual(["80–100 %", "CDI", "Plus tard"]);
    // La carte de la maquette : logo, poste, « entreprise · lieu », puces, anneau ; rien d'autre.
    expect(cards[0]!.findAll("button")).toHaveLength(0);
    expect(cards[0]!.element.tagName).toBe("A");
  });

  it("hors du tri par jour, une liste à plat sous « En préparation »", async () => {
    mockOffers(page([offer(1, "Lettre en cours", { status: "preparing" }), offer(2, "Nouvelle")]));
    const wrapper = await mountAt("/offres?tri=score");
    expect(wrapper.findAll("[data-test=offer-day] .offer-day-name").map((h) => h.text())).toEqual(["En préparation"]);
  });
});

describe("« Afficher aussi » : Écartées et Expirées (docs/139 étapes 5c et 5e)", () => {
  it("allumés, À traiter demande aussi les écartées et les expirées, et des pastilles le disent", async () => {
    const wrapper = await mountAt("/offres?ecartees=montrer&expirees=montrer");
    expect(lastQuery()).toMatchObject({ view: "pending", with_filtered_out: true, with_expired: true });
    expect(wrapper.findAll("[data-test=filter-chips] li").map((c) => c.text())).toEqual([
      "Avec les offres écartées",
      "Avec les offres expirées",
    ]);
    await mountAt("/offres");
    expect(lastQuery().with_filtered_out).toBeUndefined();
    expect(lastQuery().with_expired).toBeUndefined();
  });
});

// Vidéo de Kevin (6.11) : sur ordinateur, l'adresse /offres/384?offre=675 (arrivé par « Retour à l'offre ») rouvrait
// toujours la 384 ; chaque clic dans la liste revenait sur elle.
describe("Offres, sous-page ouverte sur ordinateur", () => {
  it("devient ?offre=, et un clic ouvre l’offre cliquée", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(path === "/api/profile-chunks" ? { data: [] } : page([offer(1, "Administrateur"), offer(2, "DevOps Engineer")])),
    );
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/offres/:id(\\d+)?", name: "offers", component: OffersView }],
    });
    await router.push("/offres/1");
    const wrapper = mount(OffersView, { global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } } });
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/offres?offre=1");
    await wrapper.findAll("[data-test=offer]")[1]!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/offres?offre=2");
    expect(wrapper.find("[data-test=offer-detail-title]").text()).toContain("DevOps Engineer");
  });
});
