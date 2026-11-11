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
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn(), PATCH: vi.fn(), POST: vi.fn() },
}));

import JobsView from "./JobsView.vue";
import OffersView from "./OffersView.vue";

const blank = { template: "<div />" };
// L'en-tête de l'application, réduit à ce que Candidatures y pose.
const Shell = { template: '<div id="topbar-page-tools" data-test="header-tools" /><RouterView />' };

afterEach(() => {
  GET.mockReset();
  document.body.innerHTML = "";
});

describe("Candidatures sur téléphone (docs/139 étape 5a, maquette Candidatures)", () => {
  it("« Alertes » et les filtres dans l’en-tête ; la recherche et « Ajouter » au-dessus des trois vues", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/offers"
          ? { data: { items: [], total: 0, counts: { to_review: 0, filtered_out: 0, later: 0, in_progress: 0, expired: 0, all: 3 }, facets: { sources: [], cantons: [], scores: [], unscored: 0 } } }
          : path === "/api/today"
            ? { data: { to_review: 4, to_follow_up: 1, alerts_waiting: 0 } }
            : { data: null },
      ),
    );
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/candidatures",
          component: JobsView,
          children: [
            { path: "offres", name: "offers", component: OffersView, meta: { tab: "offres" } },
            { path: "suivi", name: "applications", component: blank, meta: { tab: "suivi" } },
            { path: "alertes", name: "alerts", component: blank, meta: { tab: "alertes" } },
            { path: "rendez-vous-orp", name: "orp-meeting", component: blank, meta: { tab: "rendez-vous" } },
          ],
        },
        { path: "/aujourdhui/tri", name: "triage", component: blank },
      ],
    });
    await router.push("/candidatures/offres");
    const wrapper = mount(Shell, { attachTo: document.body, global: { plugins: [router], stubs: { ContactsPanel: true } } });
    await flushPromises();

    const header = wrapper.find("[data-test=header-tools]");
    expect(header.find("[data-test=jobs-alerts]").text()).toBe("Alertes");
    const filters = header.find("[data-test=filters-toggle]");
    expect(filters.attributes("aria-label")).toBe("Filtres");
    expect(filters.text()).toBe("");

    // Les vues en contrôle segmenté ; la vue ouverte porte aria-current.
    const segments = wrapper.findAll(".jobs-segments a");
    expect(segments.map((s) => s.text())).toEqual(["Offres", "Envoyées", "Rendez-vous"]);
    expect(segments[0]!.attributes("aria-current")).toBe("page");

    // Au-dessus des vues : la recherche (C4) et « Ajouter » compact (C10).
    const tools = wrapper.find("#jobs-tools");
    expect(tools.find("[data-test=search]").attributes("placeholder")).toBe("Poste, entreprise, lieu");
    expect(tools.find("[data-test=manual-open]").text()).toBe("Ajouter");
    expect(tools.find("[data-test=add-menu]").exists()).toBe(false);
    // « Postuler spontanément » : une ligne du groupe « Autres offres », au bas de la liste (PR 35).
    expect(wrapper.find("[data-test=spontaneous-open]").classes()).toContain("offers-other-row");

    // Sur Envoyées, pas d'outils d'offres ; « Alertes » reste.
    await router.push("/candidatures/suivi");
    await flushPromises();
    expect(wrapper.find("#jobs-tools").element.children).toHaveLength(0);
    expect(wrapper.find("[data-test=filters-toggle]").exists()).toBe(false);
    expect(wrapper.find("[data-test=header-tools] [data-test=jobs-alerts]").exists()).toBe(true);
    wrapper.unmount();
  });
});
