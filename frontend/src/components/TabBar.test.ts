import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../api/client", () => ({ api: { GET: () => Promise.resolve({ data: { to_review: 4 } }) } }));
vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/suivi") }) }));

import TabBar from "./TabBar.vue";

describe("La barre d'onglets du téléphone (docs/92)", () => {
  it("les deux pages, la page en cours, les offres à examiner ; cachée sur les écrans de travail", async () => {
    const view = { template: "<div />" };
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/candidatures/offres/:id/preparer", name: "preparation", component: view },
        { path: "/:any(.*)*", name: "any", component: view },
      ],
    });
    await router.push("/candidatures/offres");
    const wrapper = mount(TabBar, { global: { plugins: [router] } });
    await flushPromises();
    const jobs = wrapper.find("[data-test=tab-jobs]");
    expect(jobs.classes()).toContain("active");
    expect(jobs.attributes("aria-current")).toBe("page");
    expect(jobs.attributes("href")).toBe("/candidatures/suivi");
    expect(jobs.text()).toContain("4");
    expect(wrapper.find("[data-test=tab-today]").attributes("href")).toBe("/aujourdhui");
    await router.push("/candidatures/offres/12/preparer");
    await flushPromises();
    expect(wrapper.find("[data-test=tab-bar]").exists()).toBe(false);
  });
});
