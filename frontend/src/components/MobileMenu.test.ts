import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import MobileMenu from "./MobileMenu.vue";

vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/suivi") }) }));

const menu = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui" },
  { path: "/candidatures", name: "jobs", label: "Candidatures" },
  { path: "/progresser", name: "progress", label: "Progresser" },
];

describe("Menu burger (docs/33 §2, docs/89)", () => {
  it("les pages seulement, avec la page en cours ; se ferme en changeant de page", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/candidatures/offres");
    const wrapper = mount(MobileMenu, {
      props: { menu, newsCount: 3 },
      global: { plugins: [router], stubs: { teleport: true } },
    });
    const burger = wrapper.find("[data-test=burger]");
    await burger.trigger("click");
    expect(burger.attributes("aria-expanded")).toBe("true");
    const jobs = wrapper.find("[data-test=burger-jobs]");
    expect(jobs.classes()).toContain("active");
    expect(jobs.attributes("href")).toBe("/candidatures/suivi");
    // Du nouveau à lire : un point, pas un chiffre (docs/90).
    expect(wrapper.find("[data-test=burger-progress] .nav-dot").attributes("aria-label")).toBe("3 nouveaux");
    // Le compte, la collecte et Réglages sont dans le menu du compte (docs/89).
    expect(wrapper.text()).not.toContain("Connecté");
    expect(wrapper.find("[data-test=burger-collect]").exists()).toBe(false);

    await router.push("/progresser/actualites");
    await flushPromises();
    expect(burger.attributes("aria-expanded")).toBe("false");
  });
});
