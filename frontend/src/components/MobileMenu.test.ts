import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import MobileMenu from "./MobileMenu.vue";

const collectNow = vi.fn();
vi.mock("../composables/useCollect", () => ({ useCollect: () => ({ running: ref(false), collectNow }) }));
vi.mock("../composables/useAuth", () => ({
  useAuth: () => ({ me: ref({ username: "kevin", auth_enabled: true }), logout: vi.fn() }),
}));
vi.mock("../composables/useProfiles", () => ({
  useProfiles: () => ({ list: ref(null), current: ref(null), choose: vi.fn() }),
}));
vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/suivi") }) }));

const menu = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui" },
  { path: "/candidatures", name: "jobs", label: "Candidatures" },
  { path: "/actualites", name: "news", label: "Actualités" },
];

describe("Menu burger (docs/33 §2)", () => {
  it("pages avec la page en cours, collecte et compte ; se ferme en changeant de page", async () => {
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
    expect(wrapper.find("[data-test=burger-news]").text()).toContain("3");
    expect(wrapper.text()).toContain("Connecté : kevin");
    expect(wrapper.find("[data-test=burger-logout]").exists()).toBe(true);

    await wrapper.find("[data-test=burger-collect]").trigger("click");
    expect(collectNow).toHaveBeenCalled();
    expect(burger.attributes("aria-expanded")).toBe("false");

    await burger.trigger("click");
    await router.push("/actualites");
    await flushPromises();
    expect(burger.attributes("aria-expanded")).toBe("false");
  });
});
