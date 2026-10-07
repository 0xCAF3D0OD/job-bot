import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import SettingsView from "./SettingsView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PUT: vi.fn() },
}));
afterEach(() => vi.resetAllMocks());

function mockGet(configured: boolean): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/notifications"
          ? { configured, server: "https://ntfy.sh" }
          : { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 10 },
    }),
  );
}

describe("SettingsView, notifications", () => {
  it("API sans la route : le dit au lieu d'afficher « non configurées »", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/notifications"
          ? { data: undefined, error: { detail: "Not Found" }, response: { status: 404 } }
          : { data: { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 10 } },
      ),
    );
    const wrapper = mount(SettingsView, { global: { stubs: { StatusPanel: true, SitesPanel: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=notifications-unknown]").text()).toContain("ne répond pas");
    expect(wrapper.text()).not.toContain("Non configurées");
  });

  it("non configurées : explique quoi faire", async () => {
    mockGet(false);
    const wrapper = mount(SettingsView, { global: { stubs: { StatusPanel: true, SitesPanel: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=notifications]").text()).toContain("réglage d'installation");
    expect(wrapper.find("[data-test=test-notification]").exists()).toBe(false);
  });

  it("configurées : envoie une notification de test", async () => {
    mockGet(true);
    POST.mockResolvedValue({ response: { status: 204 } });
    const wrapper = mount(SettingsView, { global: { stubs: { StatusPanel: true, SitesPanel: true } } });
    await flushPromises();
    await wrapper.find("[data-test=test-notification]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/notifications/test");
    expect(wrapper.find("[data-test=notifications] [role=status]").text()).toContain("Notification envoyée");
  });
});

describe("SettingsView, date limite ORP", () => {
  it("enregistre le jour de remise", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/notifications"
            ? { configured: false, server: "https://ntfy.sh" }
            : { orp_monthly_target: 20, notify_score_threshold: 70, llm_monthly_budget_chf: 10, orp_due_day: 5 },
      }),
    );
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: {} } as never);
    const wrapper = mount(SettingsView, { global: { stubs: { StatusPanel: true, SitesPanel: true } } });
    await flushPromises();
    await wrapper.find("[data-test=due-day]").setValue(10);
    await wrapper.find("[data-test=settings-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", {
      body: { orp_monthly_target: 20, notify_score_threshold: 70, llm_monthly_budget_chf: 10, orp_due_day: 10 },
    });
  });
});
