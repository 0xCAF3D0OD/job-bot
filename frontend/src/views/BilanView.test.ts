import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import BilanView from "./BilanView.vue";

describe("Bilan, trois sous-onglets (docs/139 étape 8, B1)", () => {
  it("ORP · Résultats · Formations, en contrôle segmenté ; le mois suit vers les Résultats", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/bilan/:rest(.*)*", component: { template: "<div />" }, meta: { tab: "formations" } }],
    });
    await router.push("/bilan/formations?mois=2026-10");
    const wrapper = mount(BilanView, { global: { plugins: [router], stubs: { PageHero: { template: "<div><slot /></div>" } } } });
    const tabs = wrapper.findAll("a");
    expect(tabs.map((a) => a.text())).toEqual(["ORP", "Résultats", "Formations"]);
    expect(tabs.map((a) => a.attributes("href"))).toEqual(["/bilan", "/bilan/resultats?mois=2026-10", "/bilan/formations"]);
    expect(wrapper.find("[aria-current=page]").text()).toBe("Formations");
    expect(wrapper.html()).not.toContain("actualites");
  });
});
