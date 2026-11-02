import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../api/client", () => ({ api: { GET: () => Promise.resolve({ data: { to_review: 4 } }) } }));
vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/suivi") }) }));
const assistant = { available: ref(true), open: ref(false) };
vi.mock("../composables/useAssistant", () => ({ useAssistant: () => assistant }));

import BottomNav from "./BottomNav.vue";

function makeRouter() {
  const view = { template: "<div />" };
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures/offres/:id/preparer", name: "preparation", component: view },
      { path: "/aujourdhui/tri", name: "triage", component: view },
      { path: "/:any(.*)*", name: "any", component: view },
    ],
  });
}

beforeEach(() => {
  assistant.available.value = true;
  assistant.open.value = false;
});

describe("La barre du bas du téléphone (docs/139, D1 et D4 du 2026-11-02)", () => {
  it("cinq onglets libellés : Accueil, Candidatures, Assistant, Bilan, Compte", async () => {
    const router = makeRouter();
    await router.push("/aujourdhui");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    const tabs = wrapper.findAll("[data-test=tab-bar] > *");
    expect(tabs.map((tab) => tab.find(".tab-bar-label").text())).toEqual(["Accueil", "Candidatures", "Assistant", "Bilan", "Compte"]);
    expect(wrapper.find("[data-test=tab-today]").attributes("href")).toBe("/aujourdhui");
    expect(wrapper.find("[data-test=tab-bilan]").attributes("href")).toBe("/bilan");
    expect(wrapper.find("[data-test=tab-account]").attributes("href")).toBe("/reglages");
    expect(wrapper.text()).not.toContain("Progresser");
  });

  it("la page en cours, les offres à examiner, le creux sous l'onglet actif ; cachée sur les écrans de travail", async () => {
    const router = makeRouter();
    await router.push("/candidatures/offres");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    const jobs = wrapper.find("[data-test=tab-jobs]");
    expect(jobs.classes()).toContain("active");
    expect(jobs.attributes("aria-current")).toBe("page");
    expect(jobs.attributes("href")).toBe("/candidatures/suivi");
    expect(jobs.text()).toContain("4");
    // Deuxième onglet sur cinq : centre à 30 %.
    const bar = wrapper.find("[data-test=tab-bar]");
    expect(bar.classes()).toContain("has-notch");
    expect(bar.attributes("style")).toContain("--notch-x: 30%");
    await router.push("/candidatures/offres/12/preparer");
    await flushPromises();
    expect(wrapper.find("[data-test=tab-bar]").exists()).toBe(false);
    // L'écran de tri (1.6.50) : pas de barre, on revient par « ← Aujourd'hui ».
    await router.push("/aujourdhui/tri");
    await flushPromises();
    expect(wrapper.find("[data-test=tab-bar]").exists()).toBe(false);
  });

  it("Compte reste actif sur le Profil", async () => {
    const router = makeRouter();
    await router.push("/profil");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=tab-account]").classes()).toContain("active");
  });

  it("Assistant ouvre et ferme le panneau ; il prend alors le rond, un autre onglet le referme", async () => {
    const router = makeRouter();
    await router.push("/aujourdhui");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    const button = wrapper.find("[data-test=tab-assistant]");
    await button.trigger("click");
    expect(assistant.open.value).toBe(true);
    expect(wrapper.find("[data-test=tab-assistant]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=tab-today]").classes()).not.toContain("active");
    expect(wrapper.find("[data-test=tab-bar]").attributes("style")).toContain("--notch-x: 50%");
    await wrapper.find("[data-test=tab-bilan]").trigger("click");
    expect(assistant.open.value).toBe(false);
  });

  it("sans assistant, quatre onglets", async () => {
    assistant.available.value = false;
    const router = makeRouter();
    await router.push("/bilan");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=tab-assistant]").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=tab-bar] > *")).toHaveLength(4);
    expect(wrapper.find("[data-test=tab-bar]").attributes("style")).toContain("--notch-x: 62.5%");
  });
});
