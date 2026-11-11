import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: (media?: string) => ({ phone: ref(!media?.includes("min-width")) }),
  useNarrow: () => ({ phone: ref(true) }),
}));
const GET = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PATCH: (...a: unknown[]) => PATCH(...a), PUT: vi.fn(), POST: vi.fn() },
}));

import OfferFilterSheet from "../components/OfferFilterSheet.vue";
import OffersView from "./OffersView.vue";

const offer = (id: number, title: string) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne, VD",
  status: "to_review",
  first_seen_at: new Date().toISOString(),
  last_seen_at: new Date().toISOString(),
  links: [],
  filter_reasons: [],
});
const counts = { to_review: 1, pending: 1, filtered_out: 0, later: 0, in_progress: 0, expired: 0, all: 1 };
const facets = { sources: [], cantons: [], scores: [] as number[], unscored: 0 };

async function mountAt(
  path: string,
  items: unknown[],
  pageFacets: typeof facets = facets,
  pageCounts: typeof counts = counts,
  paged: { total: number; more: unknown[] } | null = null,
) {
  GET.mockImplementation((p: string, init?: { params?: { query?: { offset?: number } } }) =>
    Promise.resolve(
      p === "/api/offers"
        ? {
            data: {
              items: paged && init?.params?.query?.offset ? paged.more : items,
              total: paged?.total ?? items.length,
              counts: pageCounts,
              facets: pageFacets,
            },
          }
        : { data: null },
    ),
  );
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/offres", component: OffersView },
      { path: "/aujourdhui/tri", name: "triage", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  // Les cibles de Teleport du téléphone (en-tête, outils de Candidatures).
  const host = mount({ template: '<div id="topbar-page-tools" /><div id="jobs-tools" /><RouterView />' }, {
    attachTo: document.body,
    global: { plugins: [router], stubs: { ContactsPanel: true } },
  });
  await flushPromises();
  return host;
}

afterEach(() => {
  GET.mockReset();
  PATCH.mockReset();
  vi.useRealTimers();
  document.body.innerHTML = "";
});

describe("Candidatures sur téléphone, étape 5d (docs/139, C6 et C9)", () => {
  it("les offres « Loin » cachées derrière la ligne « Loin de ton profil » d’« Autres offres » (PR 35)", async () => {
    const close = { ...offer(1, "DevOps Engineer"), score: 82 };
    const far = { ...offer(2, "Data Engineer"), score: 41 };
    const unscored = { ...offer(3, "SRE"), score: null };
    // Les tranches de 5 points du serveur : 2 offres sous 50 dans toute la liste, 1 au-dessus.
    const scores = Array.from({ length: 20 }, (_, i) => (i === 8 ? 2 : i === 16 ? 1 : 0));
    const host = await mountAt("/offres", [close, far, unscored], { ...facets, scores });
    const titles = () => host.findAll("[data-test=offer] [data-test=list-card-title]").map((t) => t.text());
    expect(titles()).toEqual(["DevOps Engineer", "SRE"]);
    const toggle = host.find("[data-test=offers-far]");
    expect(toggle.text()).toBe("Loin de ton profil, 2 offres, notées plus bas");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    // « Afficher n offres » du tri compte la liste montrée : 3 au total, moins les 2 « Loin » cachées.
    const sheetTotal = () => host.findComponent(OfferFilterSheet).props("total");
    expect(sheetTotal()).toBe(1);
    await toggle.trigger("click");
    expect(titles()).toEqual(["DevOps Engineer", "Data Engineer", "SRE"]);
    expect(sheetTotal()).toBe(3);
    // Ouverte (Kevin, 10.11) : même titre, « n offres affichées », chevron vers le haut.
    expect(toggle.text()).toBe("Loin de ton profil, 2 offres affichées");
    expect(toggle.find("[data-icon=chevron-up]").exists()).toBe(true);
    expect(toggle.attributes("aria-expanded")).toBe("true");
  });

  it("les offres expirées : la ligne « Expirées » d’« Autres offres », seulement s’il y en a (PR 35)", async () => {
    const none = await mountAt("/offres", [offer(1, "DevOps Engineer")]);
    expect(none.find("[data-test=offers-expired]").exists()).toBe(false);
    document.body.innerHTML = "";
    const host = await mountAt("/offres", [offer(1, "DevOps Engineer")], facets, { ...counts, expired: 3 });
    const link = host.find("[data-test=offers-expired]");
    expect(link.text()).toBe("Expirées, 3 offres, pour mémoire");
    expect(link.attributes("aria-expanded")).toBe("false");
    await link.trigger("click");
    await flushPromises();
    expect(GET.mock.calls.at(-1)?.[1]).toMatchObject({ params: { query: { with_expired: true } } });
    expect(host.find("[data-test=offers-expired]").text()).toBe("Expirées, 3 offres affichées");
    expect(host.find("[data-test=offers-expired]").attributes("aria-expanded")).toBe("true");
  });

  it("bas de liste (PR 35) : « Afficher n offres de plus · m restantes », 20 par appui, focus sur la première nouvelle", async () => {
    const page1 = [offer(1, "DevOps Engineer"), offer(2, "SRE")];
    const page2 = [offer(3, "Data Engineer")];
    const host = await mountAt("/offres", page1, facets, counts, { total: 3, more: page2 });
    const more = host.get("[data-test=offers-more]");
    expect(more.text()).toBe("Afficher 1 offre de plus · 1 restante");
    expect(more.get("strong").text()).toBe("Afficher 1 offre de plus");
    await more.trigger("click");
    await flushPromises();
    expect(GET.mock.calls.at(-1)?.[1]).toMatchObject({ params: { query: { limit: 20, offset: 2 } } });
    expect(document.activeElement?.closest("[data-offer-row]")?.getAttribute("data-offer-row")).toBe("3");
    // Tout est chargé : plus de bouton ; « Postuler spontanément » reste dans « Autres offres ».
    expect(host.find("[data-test=offers-more]").exists()).toBe(false);
    expect(host.get("[data-test=spontaneous-open]").text()).toBe("Postuler spontanément, À une entreprise sans offre publiée");
  });

  it("un filtre de note posé : les offres « Loin » restent dans la liste, sans le lien", async () => {
    const far = { ...offer(2, "Data Engineer"), score: 41 };
    const scores = Array.from({ length: 20 }, (_, i) => (i === 8 ? 1 : 0));
    const host = await mountAt("/offres?note=0-49", [far], { ...facets, scores });
    expect(host.findAll("[data-test=offer]")).toHaveLength(1);
    expect(host.find("[data-test=offers-far]").exists()).toBe(false);
  });

  it("comme la maquette : ni phrase au-dessus de la liste, ni « Il te manque » ; deux initiales sur le carré", async () => {
    const gap = { ...offer(1, "Data Engineer"), company: "Léman Data SA", keywords_asks: [{ text: "Spark", covered: false }] };
    const host = await mountAt("/offres", [gap]);
    expect(host.find("[data-test=offers-sentence]").exists()).toBe(false);
    expect(host.find("[data-test=offer]").text()).not.toContain("Spark");
    expect(host.find("[data-test=offer] .list-card-logo").text()).toBe("LD");
  });

  it("les offres en préparation sous leur titre de section, sans étiquette, « Préparer » ni « ⋯ » ; la ville sans canton", async () => {
    const preparing = { ...offer(1, "Senior Platform Engineer"), status: "preparing" };
    const host = await mountAt("/offres?tri=score", [preparing, offer(2, "Data Engineer")]);
    const days = host.findAll("[data-test=offer-day]");
    expect(days).toHaveLength(1);
    expect(days[0]!.text()).toContain("En préparation");
    // La carte commune (maquette du 7.11.2026) : ni « Préparer » ni « ⋯ », rien d'autre que les puces et l'anneau.
    expect(host.findAll("[data-test=offer] button")).toHaveLength(0);
    expect(host.find("[data-test=offer]").text()).not.toContain("En préparation");
    expect(host.find("[data-test=offer] .list-card-sub").text()).toBe("Acme SA · Lausanne");
  });

  it("un logo qui ne charge pas : les initiales colorées à la place", async () => {
    const host = await mountAt("/offres", [{ ...offer(1, "Data Engineer"), company: "Léman Data SA", has_logo: true }]);
    await host.find("[data-test=offer] .list-card-logo img").trigger("error");
    expect(host.find("[data-test=offer] .list-card-logo img").exists()).toBe(false);
    expect(host.find("[data-test=offer] .list-card-logo").text()).toBe("LD");
  });

  it("aucune offre avec des filtres : ce qui filtre, en mots, et « Modifier les filtres »", async () => {
    const wrapper = await mountAt("/offres?note=70&taux=80", []);
    const empty = wrapper.find("[data-test=offers-empty]");
    expect(empty.find(".face-state-title").text()).toBe("Aucune offre avec ces filtres");
    expect(empty.text()).toContain("Note minimale : Proche et plus, Taux minimum : 80 %. Élargis un critère pour voir plus d’offres.");
    expect(empty.find("[data-test=offers-edit-filters]").classes()).toContain("primary");
    // Les 4 personnages du logo (maquette AucuneOffre, §15) : la scène « aucune-offre », 330 px, seule sur l'écran.
    const person = empty.find("[data-illustration=troupe]");
    expect(person.attributes("data-scene")).toBe("aucune-offre");
    expect(person.attributes("width")).toBe("330");
    expect(wrapper.find("[data-mood-animation]").exists()).toBe(false);
    expect(wrapper.find(".face-mark").exists()).toBe(false);
    wrapper.unmount();
  });

  it("connexion perdue : la phrase des offres et « Réessayer »", async () => {
    GET.mockImplementation((p: string) => (p === "/api/offers" ? Promise.reject(new TypeError("Failed to fetch")) : Promise.resolve({ data: null })));
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/offres", component: OffersView }] });
    await router.push("/offres");
    const wrapper = mount({ template: '<div id="topbar-page-tools" /><div id="jobs-tools" /><RouterView />' }, {
      attachTo: document.body,
      global: { plugins: [router], stubs: { ContactsPanel: true } },
    });
    await flushPromises();
    const error = wrapper.find("[data-test=network-error]");
    expect(error.find(".face-state-title").text()).toBe("Connexion perdue");
    expect(error.text()).toContain("Impossible de charger les offres. Vérifie ta connexion, puis réessaie.");
    expect(error.find("[data-test=network-retry]").classes()).toContain("primary");
    // Ni « Aucune offre à traiter. » ni « Postuler spontanément » : on ne sait rien des offres.
    expect(wrapper.find(".offers-sentence").exists()).toBe(false);
    expect(wrapper.find("[data-test=spontaneous-open]").exists()).toBe(false);
    wrapper.unmount();
  });
});

describe("Connexion perdue après un premier chargement (maquette ErreurConnexion, 2026-11-06)", () => {
  it("l’erreur seule, sans l’ancienne liste ; « Réessayer » montre l’attente jusqu’à la réponse", async () => {
    const host = await mountAt("/offres", [offer(1, "Développeur")]);
    expect(host.find(".offer-cards").exists()).toBe(true);
    const router = (host.vm as unknown as { $router: ReturnType<typeof createRouter> }).$router;
    GET.mockImplementation((p: string) => (p === "/api/offers" ? Promise.reject(new TypeError("Failed to fetch")) : Promise.resolve({ data: null })));
    await router.push("/offres?q=dev");
    await flushPromises();
    expect(host.find("[data-test=network-error]").exists()).toBe(true);
    expect(host.find(".offer-cards").exists()).toBe(false);
    // Le serveur répond lentement : le feston d'attente, ni l'erreur ni la liste.
    let answer: (value: unknown) => void = () => undefined;
    GET.mockImplementation((p: string) => (p === "/api/offers" ? new Promise((r) => (answer = r)) : Promise.resolve({ data: null })));
    await host.find("[data-test=network-retry]").trigger("click");
    await flushPromises();
    const waiting = host.find("[data-test=network-waiting]");
    expect(waiting.find(".face-state-title").text()).toBe("Chargement…");
    expect(waiting.text()).toContain("On récupère tes offres.");
    expect(host.find("[data-test=network-error]").exists()).toBe(false);
    expect(host.find(".offer-cards").exists()).toBe(false);
    answer({ data: { items: [offer(1, "Développeur")], total: 1, counts, facets } });
    await flushPromises();
    expect(host.find("[data-test=network-waiting]").exists()).toBe(false);
    expect(host.find(".offer-cards").exists()).toBe(true);
    host.unmount();
  });
});

describe("La fiche d’une offre, une sous-page sur téléphone (docs/139 étape 6a, O1)", () => {
  async function mountNamed(path: string, items: unknown[]) {
    GET.mockImplementation((p: string) =>
      Promise.resolve(p === "/api/offers" ? { data: { items, total: items.length, counts, facets } } : { data: null }),
    );
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/candidatures/offres/:id(\\d+)?", name: "offers", component: OffersView }],
    });
    await router.push(path);
    const host = mount({ template: '<div id="topbar-page-tools" /><div id="jobs-tools" /><RouterView />' }, {
      attachTo: document.body,
      global: { plugins: [router], stubs: { ContactsPanel: true } },
    });
    await flushPromises();
    return { host, router };
  }

  it("ouvrir une offre mène à /candidatures/offres/12 avec les filtres ; le retour ramène à la liste", async () => {
    const { host, router } = await mountNamed("/candidatures/offres?tri=score", [offer(12, "DevOps Engineer")]);
    await host.find("[data-test=offer]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres/12?tri=score");
    expect(host.find("[data-test=offer-subhead]").exists()).toBe(true);
    await host.find("[data-test=back-detail]").trigger("click");
    await flushPromises();
    await new Promise((r) => setTimeout(r, 0));
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres?tri=score");
    expect(host.find("[data-test=offer-detail]").exists()).toBe(false);
  });

  it("un lien ?offre=12 devient la sous-page ; arrivé directement, le retour remplace l’adresse", async () => {
    const { host, router } = await mountNamed("/candidatures/offres?offre=12", [offer(12, "DevOps Engineer")]);
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres/12");
    expect(host.find("[data-test=offer-detail]").exists()).toBe(true);
    await host.find("[data-test=back-detail]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres");
  });
});
