import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter, type Router } from "vue-router";

import { fromQuery, toQuery } from "../composables/useOfferFilters";
import OffersView from "./OffersView.vue";

const GET = vi.fn();
const PATCH = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    PUT: (...args: unknown[]) => PUT(...args),
    GET: (...args: unknown[]) => GET(...args),
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
  snippet: "Gérer l'infrastructure.",
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
      counts: { to_review: 5, filtered_out: 2, later: 0, in_progress: 0, expired: 3, all: 7 },
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
    routes: [{ path: "/offres", component: OffersView }],
  });
  await router.push(path);
  const wrapper = mount(OffersView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
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

describe("filtres dans l'adresse", () => {
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
      view: "to_review",
    });
  });
});

describe("OffersView", () => {
  it("transmet les filtres de l'adresse à l'API", async () => {
    await mountAt("/offres?canton=VD&taux=80&site=jobup&externe=1&q=linux");
    expect(lastQuery()).toMatchObject({
      view: "to_review",
      cantons: ["VD"],
      min_rate: 80,
      sources: ["jobup"],
      external_only: true,
      q: "linux",
    });
  });

  it("un clic sur un filtre met à jour l'adresse et recharge", async () => {
    const wrapper = await mountAt("/offres");
    expect(wrapper.find("[data-test=view-filtered_out]").text()).toContain("2");
    await wrapper.find("[data-test=canton-VD]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ canton: ["VD"] });
    expect(lastQuery()).toMatchObject({ cantons: ["VD"] });

    await wrapper.find("[data-test=source-indeed]").trigger("change");
    await wrapper.find("[data-test=view-all]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ canton: ["VD"], site: ["indeed"], statut: "all" });
    expect(wrapper.find("[data-test=reset]").text()).toContain("(2)");

    await wrapper.find("[data-test=reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ statut: "all" });
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
    expect(cards[0]?.text()).toContain("chez l'employeur");
    expect(cards[0]?.text()).toContain("à noter");
    expect(cards[1]?.find(".badge.reason").text()).toBe("Type : stage (« stage »)");

    await cards[0]?.trigger("click");
    const apply = wrapper.find("[data-test=apply]");
    expect(apply.text()).toContain("Postuler chez l'employeur");
    expect(apply.attributes("rel")).toBe("noopener noreferrer");
    expect(wrapper.find("[data-test=description]").text()).toBe("Notre client recherche un ingénieur.");
    expect(wrapper.text()).toContain("Temporaire");

    await wrapper.find("[data-test=close-detail]").trigger("click");
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);

    await cards[1]?.trigger("click");
    expect(wrapper.find("[data-test=reasons]").text()).toContain("Type : stage");
  });
});

describe("note et résumé", () => {
  it("carte avec note et résumé, détail avec points forts reliés aux blocs", async () => {
    mockOffers(
      page([
        offer(9, "Ingénieur système", {
          score: 82,
          summary_role: "Exploiter des serveurs Linux",
          summary_asks: "5 ans Linux, Ansible",
          summary_offers: "80-100 %, salaire non précisé",
          strengths: [{ text: "Linux solide", chunk_ids: [1] }],
          gaps: [{ text: "Pas d'Ansible", chunk_ids: [] }],
          scored_at: "2026-10-05T08:00:00Z",
        }),
        offer(10, "Pas notée"),
      ]),
    );
    const wrapper = await mountAt("/offres?tri=score&note=70");
    expect(lastQuery()).toMatchObject({ sort: "score", min_score: 70 });
    const [scored, unscored] = wrapper.findAll("[data-test=offer]");
    expect(scored?.find("[data-test=score]").text()).toBe("82");
    expect(scored?.find("[data-test=score]").classes()).toContain("high");
    expect(scored?.find("[data-test=summary]").text()).toContain("Demande5 ans Linux, Ansible");
    expect(unscored?.text()).toContain("à noter");

    await scored?.trigger("click");
    expect(wrapper.find("[data-test=ai]").text()).toContain("82/100");
    expect(wrapper.find("[data-test=strengths]").text()).toContain("Bloc : Linux");
    expect(wrapper.find("[data-test=gaps]").text()).toContain("Pas d'Ansible");
  });
});

describe("tri et candidature", () => {
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
    POST.mockResolvedValue({ data: { id: 9, company: "Acme SA" } });
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
    await wrapper.find("[data-test=mark-applied]").trigger("click");
    await flushPromises();
    await wrapper.find("form.application-form").trigger("submit");
    await flushPromises();
    const [path, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(path).toBe("/api/applications");
    expect(opts.body).toMatchObject({ offer_id: 1, company: "Acme SA", rate_text: "plein temps ou temps partiel (80-100 %)" });
    expect(wrapper.text()).toContain("Candidature chez Acme SA enregistrée.");
  });
});

describe("offres expirées", () => {
  it("onglet Expirées et bandeau dans le détail", async () => {
    mockOffers(
      page([offer(4, "Ingénieur cloud", { expired_at: "2026-10-04T08:00:00Z", expiry_source: "age" })]),
    );
    const wrapper = await mountAt("/offres?statut=expired");
    expect(lastQuery().view).toBe("expired");
    expect(wrapper.text()).toContain("Expirées");
    await wrapper.find("[data-test=offer]").trigger("click");
    expect(wrapper.find("[data-test=expired]").text()).toContain("Probablement expirée");
  });
});

describe("filtres au choix", () => {
  it("affiche les filtres enregistrés, masque et remet à zéro un filtre actif", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offer-filters"
          ? { data: { visible: ["sources", "rate"] } }
          : path === "/api/profile-chunks"
            ? { data: [] }
            : page([offer(1, "Ingénieur système")]),
      ),
    );
    PUT.mockResolvedValue({ data: { visible: ["sources"] } });
    const wrapper = await mountAt("/offres?taux=80");
    const panel = wrapper.find("[data-test=filters]");
    expect(panel.text()).toContain("Sites");
    expect(panel.text()).not.toContain("Cantons");
    expect(panel.text()).toContain("Taux minimum");

    await wrapper.find("[data-test=customize]").trigger("click");
    await wrapper.find("[data-test=show-rate]").setValue(false);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/offer-filters", { body: { visible: ["sources"] } });
    expect(router.currentRoute.value.query.taux).toBeUndefined();
    expect(wrapper.find("[data-test=filters]").text()).not.toContain("Les offres sans taux indiqué");
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
          company_address: "Chemin de l'Exemple 10\n1206 Genève",
          company_address_source: "page",
        }),
      ]),
    );
    const wrapper = await mountAt("/offres?statut=later");
    await wrapper.find("[data-test=offer]").trigger("click");
    expect(wrapper.find("[data-test=status-pill]").text()).toBe("Plus tard");
    expect(wrapper.find("[data-test=later]").exists()).toBe(false);
    expect(wrapper.find("[data-test=address]").text()).toContain("Chemin de l'Exemple 10, 1206 Genève");
    expect(wrapper.find("[data-test=address]").text()).toContain("annonce");

    await wrapper.find("[data-test=more]").trigger("click");
    expect(wrapper.find("[data-test=back-to-review]").exists()).toBe(true);

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
          : path === "/api/profile-chunks"
            ? { data: [] }
            : page([offer(1, "Ingénieur système")]),
      ),
    );
    POST.mockResolvedValue({ data: { company_address: "Rue 2\n1206 Genève", company_address_source: "registry" } });
    const wrapper = await mountAt("/offres");
    await wrapper.find("[data-test=offer]").trigger("click");
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
  it("affiche les pastilles, demandes non couvertes en orange ; sinon les phrases", async () => {
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
    const keywords = cards[0]!.find("[data-test=keywords]");
    expect(keywords.text()).toContain("DevOps");
    expect(keywords.find(".kw.gap").text()).toBe("allemand B2");
    expect(keywords.findAll(".kw.offer").map((k) => k.text())).toEqual(["80-100 %", "CDI"]);
    expect(cards[1]!.find("[data-test=summary]").text()).toContain("Phrase complète du poste");
  });
});
