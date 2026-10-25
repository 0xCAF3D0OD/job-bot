import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import BilanView from "./BilanView.vue";

describe("Bilan, deux onglets (1.6.25)", () => {
  it("Résultats et Formations ; plus d'Actualités ni de pastille", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/bilan/:rest(.*)*", component: { template: "<div />" } }],
    });
    await router.push("/bilan");
    const wrapper = mount(BilanView, { global: { plugins: [router], stubs: { PageHero: { template: "<div><slot /></div>" } } } });
    const tabs = wrapper.findAll("nav a").map((a) => a.text());
    expect(tabs).toEqual(["Résultats", "Formations"]);
    expect(wrapper.find(".tab-count").exists()).toBe(false);
    expect(wrapper.html()).not.toContain("actualites");
  });
});
