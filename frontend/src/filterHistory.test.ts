import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent, h, ref } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { describe, expect, it } from "vitest";

import BottomSheet from "./components/BottomSheet.vue";
import OfferFilterChips from "./components/OfferFilterChips.vue";
import OfferFilterPanel from "./components/OfferFilterPanel.vue";
import OfferFilterSheet from "./components/OfferFilterSheet.vue";
import { activeChips, useOfferFilters } from "./composables/useOfferFilters";

const facets = { sources: [], cantons: [], scores: [], unscored: 0, sure: 1, provisional: 1, rates: [], contracts: [] };
const counts = { pending: 38, to_review: 12, later: 4, in_progress: 2, filtered_out: 3, expired: 1, all: 50 };
// history.back() de jsdom part dans une tâche à part : on laisse passer l’événement popstate et la navigation.
const settle = async () => {
  for (let i = 0; i < 3; i += 1) {
    await new Promise((resolve) => setTimeout(resolve, 20));
    await flushPromises();
  }
};

// La page Offres réduite à ses filtres : la feuille du téléphone, ou le panneau de l’ordinateur (monté en v-if), et
// les pastilles sous la barre.
async function mountOffers(start: string, desktop = false) {
  const open = ref(false);
  const Host = defineComponent({
    setup() {
      const { filters, update, reset } = useOfferFilters();
      return () =>
        h("div", [
          h(OfferFilterChips, { chips: activeChips(filters.value), onUpdate: (patch: object) => update(patch, true), onReset: () => reset(true) }),
          desktop
            ? open.value
              ? h(OfferFilterPanel, { filters: filters.value, facets, total: 3, counts, onUpdate: update, onReset: reset, onClose: () => (open.value = false) })
              : null
            : h(OfferFilterSheet, { open: open.value, filters: filters.value, facets, total: 3, counts, onUpdate: update, onReset: reset, onClose: () => (open.value = false) }),
        ]);
    },
  });
  const router = createRouter({ history: createWebHistory(), routes: [{ path: "/offres", name: "offers", component: Host }] });
  sessionStorage.clear();
  await router.push(start);
  await router.isReady();
  const wrapper = mount({ template: "<router-view />" }, { global: { plugins: [router] }, attachTo: document.body });
  await settle();
  const show = async () => {
    open.value = true;
    await settle();
  };
  return { wrapper, router, open, show };
}

describe("Filtres et historique (Kevin, 17.11)", () => {
  it("téléphone : « Nouvelles » choisi dans la feuille reste après la fermeture (le bug de « Gardées »)", async () => {
    const { wrapper, router, open, show } = await mountOffers("/offres?statut=later");
    await show();
    await wrapper.find("[data-test=sheet-view-to_review]").trigger("click");
    await settle();
    await wrapper.find("[data-test=sheet-show]").trigger("click");
    await settle();
    expect(open.value).toBe(false);
    expect(router.currentRoute.value.query.statut).toBe("to_review");
    // Une seule entrée pour cette application : retour ramène les filtres d’avant.
    router.back();
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    wrapper.unmount();
  });

  it("téléphone : la note et le statut changés ensemble, fermés par la croix, restent ; une entrée pour les deux", async () => {
    const { wrapper, router, show } = await mountOffers("/offres?statut=later");
    await show();
    await wrapper.find("[data-test=sheet-view-to_review]").trigger("click");
    await settle();
    await wrapper.find("[data-test=sheet-score-75]").trigger("click");
    await settle();
    await wrapper.find("[data-test=sheet-close]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query).toMatchObject({ statut: "to_review", note: "75" });
    router.back();
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    expect(router.currentRoute.value.query.note).toBeUndefined();
    wrapper.unmount();
  });

  it("téléphone : retour pendant que la feuille est ouverte applique aussi (Kevin, 17.11, 13 h 43) ; retour encore ramène les filtres d’avant", async () => {
    const { wrapper, router, open, show } = await mountOffers("/offres?statut=later");
    await show();
    await wrapper.find("[data-test=sheet-view-to_review]").trigger("click");
    await settle();
    // Pas de clignotement (14 h 07) : le routeur ne repasse jamais par les filtres d’avant.
    const seen: unknown[] = [];
    const stop = router.afterEach((to) => void seen.push(to.query.statut));
    window.history.back();
    await settle();
    stop();
    expect(seen).not.toContain("later");
    expect(open.value).toBe(false);
    expect(router.currentRoute.value.query.statut).toBe("to_review");
    expect(window.history.state?.sheet).toBeUndefined();
    router.back();
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    wrapper.unmount();
  });

  it("téléphone : retour pendant l’ouverture, sans changement, ferme seulement", async () => {
    const { wrapper, router, open, show } = await mountOffers("/offres?statut=later");
    const before = window.history.state?.position;
    await show();
    window.history.back();
    await settle();
    expect(open.value).toBe(false);
    expect(router.currentRoute.value.query.statut).toBe("later");
    expect(window.history.state?.position).toBe(before);
    wrapper.unmount();
  });

  it("téléphone : fermée sans changement, la feuille n’ajoute aucune entrée", async () => {
    const { wrapper, router, show } = await mountOffers("/offres?statut=later");
    const before = window.history.state?.position;
    await show();
    await wrapper.find("[data-test=sheet-close]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    expect(window.history.state?.sheet).toBeUndefined();
    expect(window.history.state?.position).toBe(before);
    wrapper.unmount();
  });

  it("ordinateur : le panneau « Plus de filtres » suit les mêmes règles", async () => {
    const { wrapper, router, open, show } = await mountOffers("/offres?statut=later", true);
    await show();
    await wrapper.find("[data-test=pop-view-to_review]").trigger("click");
    await settle();
    // Retour pendant l’ouverture applique, comme sur téléphone.
    window.history.back();
    await settle();
    expect(open.value).toBe(false);
    expect(router.currentRoute.value.query.statut).toBe("to_review");
    router.back();
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    await show();
    await wrapper.find("[data-test=pop-view-to_review]").trigger("click");
    await settle();
    open.value = false;
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("to_review");
    router.back();
    await settle();
    expect(router.currentRoute.value.query.statut).toBe("later");
    wrapper.unmount();
  });

  it("les pastilles et « Tout effacer » sous la barre appliquent tout de suite, une entrée chacun", async () => {
    const { wrapper, router } = await mountOffers("/offres?statut=later&note=75");
    await wrapper.find("[data-test=chip-remove-score]").trigger("click");
    await settle();
    expect(router.currentRoute.value.query).toEqual({ statut: "later" });
    router.back();
    await settle();
    expect(router.currentRoute.value.query).toEqual({ statut: "later", note: "75" });
    wrapper.unmount();
  });

  it("Envoyées : le tri seul n’entre pas dans l’historique (préférence du compte, 14 h 07)", async () => {
    const open = ref(false);
    const Page = () => h(BottomSheet, { open: open.value, title: "Filtres", onClose: () => (open.value = false) });
    const router = createRouter({ history: createWebHistory(), routes: [{ path: "/candidatures/suivi", name: "applications", component: Page }] });
    await router.push("/candidatures/suivi?statut=relancer");
    await router.isReady();
    const wrapper = mount({ template: "<router-view />" }, { global: { plugins: [router] }, attachTo: document.body });
    const before = window.history.state?.position;
    open.value = true;
    await settle();
    await router.replace({ query: { ...router.currentRoute.value.query, tri: "anciennes" } });
    await settle();
    open.value = false;
    await settle();
    // Pas d’entrée gardée : on est revenu à l’entrée d’avant (la page y remet son tri, ApplicationsView).
    expect(window.history.state?.position).toBe(before);
    expect(window.history.state?.sheet).toBeUndefined();
    wrapper.unmount();
  });
});
