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
          { path: "rendez-vous-orp", name: "orp-meeting", component: child, meta: { tab: "rendez-vous" } },
        ],
      },
    ],
  });
  await router.push(path);
  const wrapper = mount({ template: "<RouterView />" }, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("JobsView (docs/19 §2, docs/139 étape 5a)", () => {
  it("trois vues À traiter · Envoyées · Rendez-vous, « Alertes » à côté du titre, pastilles, mois conservé", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/today" ? { to_review: 5, pending: 12, to_follow_up: 2, alerts_waiting: 1 } : { incomplete: 1 } }),
    );
    const { wrapper, router } = await mountJobs("/candidatures/alertes?mois=2026-09");
    // Le titre reste celui du menu (docs/88) : le segment choisi dit où l'on est.
    expect(wrapper.find("h1").text()).toBe("Candidatures");
    const tabs = ["offres", "suivi", "rendez-vous"].map((k) => wrapper.find(`[data-test=jobs-tab-${k}]`));
    // Envoyées : à relancer (2) + lignes ORP à compléter (1), docs/22 §1.
    expect(tabs.map((t) => t.text())).toEqual(["À traiter 12", "Envoyées 3", "Rendez-vous"]);
    expect(wrapper.find("[data-test=jobs-tab-alertes]").exists()).toBe(false);
    // Alertes : un lien à côté du titre (C1), marqué quand on y est.
    const alerts = wrapper.find(".jobs-title [data-test=jobs-alerts]");
    expect(alerts.text()).toBe("Alertes1");
    expect(alerts.attributes("aria-current")).toBe("page");
    expect(tabs.some((t) => t.attributes("aria-current") === "page")).toBe(false);
    expect(tabs[1]!.attributes("href")).toBe("/candidatures/suivi?mois=2026-09");
    expect(wrapper.find("[data-test=child]").exists()).toBe(true);

    await tabs[0]!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("offers");
    expect(wrapper.find("[data-test=jobs-tab-offres]").attributes("aria-current")).toBe("page");
    expect(wrapper.find("[data-test=jobs-alerts]").attributes("aria-current")).toBeUndefined();
    expect(GET).toHaveBeenCalledTimes(6); // pastilles et recherches suivies relues au changement de vue
  });

  it("l'en-tête suit la largeur de l'onglet : Offres à 1 280 px, les autres à 1 020 (1.6.29)", async () => {
    GET.mockResolvedValue({ data: {} });
    const { wrapper, router } = await mountJobs("/candidatures/offres");
    expect(wrapper.find(".jobs-head").classes()).toContain("wide");
    await router.push("/candidatures/suivi");
    await flushPromises();
    expect(wrapper.find(".jobs-head").classes()).not.toContain("wide");
  });
});
