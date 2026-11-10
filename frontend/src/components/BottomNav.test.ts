import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../api/client", () => ({ api: { GET: () => Promise.resolve({ data: { to_review: 2, pending: 7, pending_near: 4 } }) } }));
vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/suivi") }) }));
const assistant = { available: ref(true), known: ref(true) };
vi.mock("../composables/useAssistant", () => ({ useAssistant: () => assistant }));

import BottomNav from "./BottomNav.vue";

function makeRouter() {
  const view = { template: "<div />" };
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/candidatures/offres/:id/preparer", name: "preparation", component: view },
      { path: "/aujourdhui/tri", name: "triage", component: view },
      { path: "/assistant", name: "assistant", component: view },
      { path: "/reglages", name: "settings", component: view },
      { path: "/notifications", name: "notifications", component: view },
      { path: "/:any(.*)*", name: "any", component: view },
    ],
  });
}

beforeEach(() => {
  assistant.available.value = true;
  assistant.known.value = true;
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
    expect(wrapper.find("[data-test=tab-account]").attributes("href")).toBe("/compte");
    expect(wrapper.text()).not.toContain("Progresser");
  });

  it("la page en cours, les offres à examiner, le creux sous l’onglet actif ; cachée sur les écrans de travail", async () => {
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
    // Les Réglages et les Notifications, pages avec leur flèche retour (Kevin, 6.11) : pas de barre.
    for (const path of ["/reglages", "/notifications"]) {
      await router.push(path);
      await flushPromises();
      expect(wrapper.find("[data-test=tab-bar]").exists()).toBe(false);
    }
  });

  it("Compte reste actif sur le Profil", async () => {
    const router = makeRouter();
    await router.push("/profil");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=tab-account]").classes()).toContain("active");
  });

  it("Assistant mène à sa page (étape 11a) et y prend le rond", async () => {
    const router = makeRouter();
    await router.push("/aujourdhui");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=tab-assistant]").attributes("href")).toBe("/assistant");
    // La mascotte dans son cercle (maquette AccueilSmile).
    expect(wrapper.find("[data-test=tab-assistant] [data-test=tab-assistant-ring] [data-test=assistant-mascot]").exists()).toBe(true);
    await router.push("/assistant");
    await flushPromises();
    const tab = wrapper.find("[data-test=tab-assistant]");
    expect(tab.classes()).toContain("active");
    expect(tab.attributes("aria-current")).toBe("page");
    expect(wrapper.find("[data-test=tab-today]").classes()).not.toContain("active");
    expect(wrapper.find("[data-test=tab-bar]").attributes("style")).toContain("--notch-x: 50%");
  });

  it("tant que la présence de l’Assistant n’est pas connue, pas de barre (AS8 : pas de saut de 5 à 4)", async () => {
    assistant.known.value = false;
    const router = makeRouter();
    await router.push("/aujourdhui");
    const wrapper = mount(BottomNav, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=tab-bar]").exists()).toBe(false);
    assistant.known.value = true;
    await flushPromises();
    expect(wrapper.findAll("[data-test=tab-bar] > *")).toHaveLength(5);
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
