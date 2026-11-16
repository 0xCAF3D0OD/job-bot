import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SentPhoneFilters from "./SentPhoneFilters.vue";

// Envoyées sur téléphone (maquette du 14 novembre, §3 et §6 ; décisions de Kevin du 14.11) : la recherche « Poste,
// entreprise, lieu » lue « Rechercher une candidature », statuts et tri dans la feuille Filtres.
const counts = { toutes: 9, relancer: 2, "sans-reponse": 3, entretien: 0, refusees: 1 };

function mountIt(props: Record<string, unknown> = {}) {
  return mount(SentPhoneFilters, {
    props: { words: "", filter: "toutes", sort: "relancer", counts, total: 9, ...props },
    global: { stubs: { teleport: true, BottomSheet: { template: "<div><slot /><slot name=\"actions\" /></div>" } } },
  });
}

describe("SentPhoneFilters", () => {
  it("le champ et son nom pour les lecteurs d'écran", () => {
    const input = mountIt().find("[data-test=search]");
    expect(input.attributes("placeholder")).toBe("Poste, entreprise, lieu");
    expect(input.attributes("aria-label")).toBe("Rechercher une candidature");
  });

  it("les statuts sans les vides, le tri en trois choix, le nombre à afficher", async () => {
    const wrapper = mountIt();
    expect(wrapper.find("[data-test=sent-status-entretien]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sent-status-relancer]").text()).toBe("À relancer · 2");
    // Planche FiltresEnvoyees : le statut choisi coché, le tri en choix cochés (trois choix, qui passent à la ligne).
    expect(wrapper.find("[data-test=sent-status-toutes]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=sent-status-toutes] .icon").exists()).toBe(true);
    expect(wrapper.find("[data-test=sent-status-relancer] .icon").exists()).toBe(false);
    expect(wrapper.find("[data-test=sent-sort-relancer]").attributes("aria-checked")).toBe("true");
    expect(wrapper.findAll("[data-test^=sent-sort-]").map((b) => b.text())).toEqual(["À relancer d’abord", "Plus récentes d’abord", "Plus anciennes d’abord"]);
    expect(wrapper.find("[data-test=sent-sheet-show]").text()).toBe("Afficher 9 candidatures");
    await wrapper.find("[data-test=sent-sort-recentes]").trigger("click");
    expect(wrapper.emitted("update:sort")).toEqual([["recentes"]]);
    await wrapper.find("[data-test=sent-sheet-reset]").trigger("click");
    expect(wrapper.emitted("reset")).toHaveLength(1);
  });

  it("l'icône dit combien de filtres sont actifs", () => {
    const toggle = mountIt({ filter: "relancer", sort: "recentes" }).find("[data-test=sent-filters-toggle]");
    expect(toggle.attributes("aria-label")).toBe("Filtres, 2 actifs");
  });
});
