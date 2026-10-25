import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import SettingsView from "./SettingsView.vue";

vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone: ref(true) }) }));
vi.mock("../api/client", () => ({
  api: {
    GET: (path: string) =>
      Promise.resolve({
        data: path === "/api/settings" ? { notify_score_threshold: 70, llm_monthly_budget_chf: 5, rhythm_days: [0, 1, 2, 3, 4] } : null,
      }),
    POST: vi.fn(),
    PUT: vi.fn(),
  },
}));

describe("Réglages sur téléphone : une longue page et ses marqueurs (docs/110)", () => {
  it("toutes les rubriques l'une sous l'autre ; un marqueur mène à sa section", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/reglages");
    const wrapper = mount(SettingsView, {
      attachTo: document.body,
      global: { plugins: [router], stubs: { SitesPanel: true, NewsSourcesPanel: true, AgendaPanel: true, ExtensionPanel: true, SessionPanel: true, AccountDataPanel: true, AiSpend: true } },
    });
    await flushPromises();
    const ids = wrapper.findAll("section.settings-section").map((s) => s.attributes("id"));
    expect(ids).toEqual(["recherche", "rythme", "notifications", "ia", "compte", "outils"]);
    const markers = wrapper.findAll("[data-test=settings-markers] a");
    expect(markers.map((m) => m.text())).toEqual(["Recherche d'emploi", "Rythme", "Notifications", "IA", "Compte", "Agenda et extension"]);
    const scroll = vi.fn();
    (document.getElementById("notifications") as HTMLElement).scrollIntoView = scroll;
    await wrapper.find("[data-test=marker-notifications]").trigger("click");
    expect(scroll).toHaveBeenCalled();
    expect(wrapper.find("[data-test=marker-notifications]").attributes("aria-current")).toBe("location");
    wrapper.unmount();
  });
});
