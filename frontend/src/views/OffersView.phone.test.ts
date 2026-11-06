import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: () => ({ phone: ref(true) }),
  useNarrow: () => ({ phone: ref(true) }),
}));
const GET = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PATCH: (...a: unknown[]) => PATCH(...a), PUT: vi.fn(), POST: vi.fn() },
}));

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
const facets = { sources: [], cantons: [], scores: [], unscored: 0 };

async function mountAt(path: string, items: unknown[]) {
  GET.mockImplementation((p: string) =>
    Promise.resolve(p === "/api/offers" ? { data: { items, total: items.length, counts, facets } } : { data: null }),
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
  it("comme la maquette : ni phrase au-dessus de la liste, ni « Il te manque » ; deux initiales sur le carré", async () => {
    const gap = { ...offer(1, "Data Engineer"), company: "Léman Data SA", keywords_asks: [{ text: "Spark", covered: false }] };
    const host = await mountAt("/offres", [gap]);
    expect(host.find("[data-test=offers-sentence]").exists()).toBe(false);
    expect(host.find("[data-test=offer-alert]").exists()).toBe(false);
    expect(host.find("[data-test=offer] .logo").text()).toBe("LD");
  });

  it("les offres en préparation sous leur titre de section, sans étiquette ni « Préparer » ; la ville sans canton", async () => {
    const preparing = { ...offer(1, "Senior Platform Engineer"), status: "preparing" };
    const host = await mountAt("/offres?tri=score", [preparing, offer(2, "Data Engineer")]);
    const days = host.findAll("[data-test=offer-day]");
    expect(days).toHaveLength(1);
    expect(days[0]!.text()).toContain("En préparation");
    expect(host.find("[data-test=status-tag]").exists()).toBe(false);
    expect(host.find("[data-test=offer] .offer-line-action").exists()).toBe(false);
    expect(host.findAll("[data-test=offer] [data-test=offer-more]")).toHaveLength(2);
    expect(host.find("[data-test=offer] .offer-line-sub").text()).toContain("Acme SA · Lausanne");
    expect(host.find("[data-test=offer] .offer-line-sub").text()).not.toContain("VD");
  });

  it("un logo qui ne charge pas : les initiales colorées à la place", async () => {
    const host = await mountAt("/offres", [{ ...offer(1, "Data Engineer"), company: "Léman Data SA", has_logo: true }]);
    await host.find("[data-test=offer] .logo img").trigger("error");
    expect(host.find("[data-test=offer] .logo img").exists()).toBe(false);
    expect(host.find("[data-test=offer] .logo").text()).toBe("LD");
  });

  it("le « ⋯ » de la carte ouvre ses actions ; « Écarter l'offre » garde « Annuler » 6 s", async () => {
    const wrapper = await mountAt("/offres", [offer(1, "DevOps Engineer")]);
    const more = wrapper.find("[data-test=offer] [data-test=offer-more]");
    expect(more.attributes("aria-label")).toBe("Actions pour DevOps Engineer");
    await more.trigger("click");
    await flushPromises();
    const sheet = wrapper.find("[data-test=offer-actions]");
    expect(sheet.find(".sheet-title").text()).toBe("DevOps Engineer");
    expect(sheet.findAll(".grouped-row-title").map((t) => t.text())).toEqual(["Écarter l'offre", "Marquer comme envoyée"]);
    // Le « ⋯ » n'ouvre pas la fiche.
    expect(wrapper.find("[data-test=offer-detail-title]").exists()).toBe(false);

    vi.useFakeTimers();
    PATCH.mockResolvedValue({ data: {} });
    await wrapper.find("[data-test=offer-action-discard] button").trigger("click");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 1 } }, body: { status: "ignored" } });
    expect(wrapper.find("[data-test=undo-status]").exists()).toBe(true);
    expect(wrapper.text()).toContain("Offre écartée.");
    vi.advanceTimersByTime(6000);
    await flushPromises();
    expect(wrapper.find("[data-test=undo-status]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("aucune offre avec des filtres : ce qui filtre, en mots, et « Modifier les filtres »", async () => {
    const wrapper = await mountAt("/offres?note=70&taux=80", []);
    const empty = wrapper.find("[data-test=offers-empty]");
    expect(empty.find(".face-state-title").text()).toBe("Aucune offre avec ces filtres");
    expect(empty.text()).toContain("Note minimale : Proche et plus, Taux minimum : 80 %. Élargis un critère pour voir plus d'offres.");
    expect(empty.find("[data-test=offers-edit-filters]").classes()).toContain("primary");
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
  it("l'erreur seule, sans l'ancienne liste ; « Réessayer » montre l'attente jusqu'à la réponse", async () => {
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

describe("La fiche d'une offre, une sous-page sur téléphone (docs/139 étape 6a, O1)", () => {
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
    await host.find("[data-test=offer] [data-test=offer-line-open]").trigger("click");
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

  it("un lien ?offre=12 devient la sous-page ; arrivé directement, le retour remplace l'adresse", async () => {
    const { host, router } = await mountNamed("/candidatures/offres?offre=12", [offer(12, "DevOps Engineer")]);
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres/12");
    expect(host.find("[data-test=offer-detail]").exists()).toBe(true);
    await host.find("[data-test=back-detail]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres");
  });
});
