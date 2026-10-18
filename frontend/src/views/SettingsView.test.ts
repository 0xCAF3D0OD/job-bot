import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { createMemoryHistory, createRouter } from "vue-router";

import SettingsView from "./SettingsView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PUT: vi.fn() },
}));
afterEach(() => vi.resetAllMocks());

// Une rubrique à la fois (docs/48 §2) : ?rubrique=… choisit ce qui s'affiche.
async function mountSettings(rubrique?: string) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push({ path: "/reglages", query: rubrique ? { rubrique } : {} });
  const wrapper = mount(SettingsView, { global: { plugins: [router], stubs: { StatusPanel: true, SitesPanel: true, PlatformPanel: true } } });
  await flushPromises();
  return { wrapper, router };
}

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
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.find("[data-test=notifications-unknown]").text()).toContain("ne répond pas");
    expect(wrapper.text()).not.toContain("Non configurées");
  });

  it("non configurées : explique quoi faire", async () => {
    mockGet(false);
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.find("[data-test=notifications]").text()).toContain("réglage d'installation");
    expect(wrapper.find("[data-test=test-notification]").exists()).toBe(false);
  });

  it("configurées : envoie une notification de test", async () => {
    mockGet(true);
    POST.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountSettings("notifications");
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
    const { wrapper } = await mountSettings();
    await wrapper.find("[data-test=due-day]").setValue(10);
    await wrapper.find("[data-test=settings-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", {
      body: { orp_monthly_target: 20, notify_score_threshold: 70, llm_monthly_budget_chf: 10, orp_due_day: 10 },
    });
  });
});

describe("SettingsView, une rubrique à la fois (docs/48)", () => {
  it("six rubriques, une seule affichée ; un ancien lien #agenda mène à Outils", async () => {
    mockGet(false);
    const { wrapper, router } = await mountSettings();
    const toc = wrapper.findAll(".settings-toc a").map((a) => a.text());
    expect(toc).toEqual(["Recherche d'emploi", "Actualités", "Notifications", "IA", "Compte", "Outils"]);
    expect(wrapper.find("[data-test=settings-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=notifications]").exists()).toBe(false);
    // Le seuil de notification est dans sa rubrique, dit en clair.
    expect(wrapper.text()).not.toContain("M'avertir d'une offre");
    await router.push({ query: { rubrique: "notifications" } });
    await flushPromises();
    expect(wrapper.text()).toContain("M'avertir d'une offre à partir de");
    expect(wrapper.find("[data-test=settings-form]").exists()).toBe(false);

    await router.push({ path: "/reglages", query: {}, hash: "#agenda" });
    await flushPromises();
    expect(wrapper.find(".settings-toc a.active").text()).toBe("Outils");
  });
});

describe("SettingsView, comptes (docs/65)", () => {
  afterEach(async () => {
    const { useAuth } = await import("../composables/useAuth");
    useAuth().me.value = null;
  });

  async function as(isOwner: boolean): Promise<void> {
    const { useAuth } = await import("../composables/useAuth");
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: isOwner, welcome: "done", demo: false };
  }

  it("compte invité : plafond de l'IA fixé, ni Plateforme ni profils d'essai", async () => {
    await as(false);
    mockGet(false);
    const { wrapper } = await mountSettings("ia");
    expect(wrapper.find("[data-test=budget-fixed]").text()).toContain("10 CHF");
    expect(wrapper.find("[data-test=budget-form]").exists()).toBe(false);
    expect(wrapper.find("[data-test=toc-plateforme]").exists()).toBe(false);
  });

  it("compte invité : active les notifications sur son téléphone", async () => {
    await as(false);
    const PUT = (await import("../api/client")).api.PUT as unknown as ReturnType<typeof vi.fn>;
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/notifications"
            ? { configured: false, server: "https://ntfy.sh", personal: true, topic: null }
            : { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 5 },
      }),
    );
    PUT.mockResolvedValue({
      data: { configured: true, server: "https://ntfy.sh", personal: true, topic: "jobbot-abc" },
    });
    const { wrapper } = await mountSettings("notifications");
    await wrapper.find("[data-test=phone-on-button]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/notifications/phone", { body: { enabled: true } });
    expect(wrapper.find("[data-test=phone-on]").text()).toContain("jobbot-abc");
  });

  it("exploitant : la rubrique Plateforme", async () => {
    await as(true);
    mockGet(false);
    const { wrapper } = await mountSettings("plateforme");
    expect(wrapper.find("[data-test=toc-plateforme]").exists()).toBe(true);
    expect(wrapper.find("[data-test=budget-form]").exists()).toBe(false);
  });
});
