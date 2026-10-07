import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import JobsView from "./JobsView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

const child = { template: "<p data-test='child' />" };

async function mountJobs(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/candidatures",
        component: JobsView,
        children: [
          { path: "offres", name: "offers", component: child, meta: { tab: "offres" } },
          { path: "suivi", name: "applications", component: child, meta: { tab: "suivi" } },
          { path: "alertes", name: "alerts", component: child, meta: { tab: "alertes" } },
        ],
      },
    ],
  });
  await router.push(path);
  const wrapper = mount({ template: "<RouterView />" }, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("JobsView (docs/19 §2)", () => {
  it("trois onglets, titre de l'onglet, pastilles, mois conservé", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? { to_review: 12, to_follow_up: 2, alerts_waiting: 1 } : { incomplete: 1 } }),
    );
    const { wrapper, router } = await mountJobs("/candidatures/alertes?mois=2026-09");
    expect(wrapper.find("h1").text()).toBe("Tes alertes emploi");
    const tabs = ["offres", "suivi", "alertes"].map((k) => wrapper.find(`[data-test=jobs-tab-${k}]`));
    // Suivi : à relancer (2) + lignes ORP à compléter (1), docs/22 §1.
    expect(tabs.map((t) => t.text())).toEqual(["Offres 12", "Suivi 3", "Alertes 1"]);
    expect(tabs[2]!.classes()).toContain("active");
    expect(tabs[1]!.attributes("href")).toBe("/candidatures/suivi?mois=2026-09");
    expect(wrapper.find("[data-test=child]").exists()).toBe(true);

    await tabs[0]!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("offers");
    expect(wrapper.find("h1").text()).toBe("Les offres pour toi");
    expect(GET).toHaveBeenCalledTimes(4); // pastilles relues au changement d'onglet
  });
});
