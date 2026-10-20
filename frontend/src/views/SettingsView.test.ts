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
          : {
              orp_monthly_target: null,
              notify_score_threshold: 70,
              llm_monthly_budget_chf: 10,
              rhythm_days: [0, 1, 2, 3, 4],
              offers_notify_mode: "daily",
              offers_notify_hour: 9,
            },
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
      body: {
        orp_monthly_target: 20,
        notify_score_threshold: 70,
        llm_monthly_budget_chf: 10,
        orp_due_day: 10,
        rhythm_pause_from: null,
        rhythm_pause_until: null,
      },
    });
  });
});

describe("SettingsView, une rubrique à la fois (docs/48)", () => {
  it("sept rubriques, une seule affichée ; un ancien lien #agenda mène à Outils", async () => {
    mockGet(false);
    const { wrapper, router } = await mountSettings();
    const toc = wrapper.findAll(".settings-toc a").map((a) => a.text());
    expect(toc).toEqual(["Recherche d'emploi", "Rythme", "Actualités", "Notifications", "IA", "Compte", "Outils"]);
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

  it("compte invité : pas de lien vers le Diagnostic (docs/108 §3)", async () => {
    await as(false);
    mockGet(false);
    const { wrapper } = await mountSettings();
    expect(wrapper.find("[data-test=diagnostic-link]").exists()).toBe(false);
    await as(true);
    const owner = await mountSettings();
    expect(owner.wrapper.find("[data-test=diagnostic-link]").exists()).toBe(true);
  });

  it("Compte : un seul titre par partie, « Se déconnecter partout » en lien (0.77.2)", async () => {
    await as(false);
    mockGet(false);
    const { wrapper } = await mountSettings("compte");
    const titles = wrapper.findAll("[data-test=settings-card] legend, [data-test=settings-card] h3").map((t) => t.text());
    expect(titles.filter((t) => t === "Connexion")).toHaveLength(1);
    expect(titles).not.toContain("Compte");
    expect(wrapper.find("[data-test=logout-all]").classes()).toContain("link");
  });

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

  it("exploitant : le plafond de l'IA s'enregistre au changement (docs/106)", async () => {
    await as(true);
    mockGet(false);
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: { llm_monthly_budget_chf: 12 } } as never);
    const { wrapper } = await mountSettings("ia");
    expect(wrapper.find("[data-test=save-budget]").exists()).toBe(false);
    const input = wrapper.find("#budget");
    await input.setValue(12);
    await input.trigger("change");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", { body: expect.objectContaining({ llm_monthly_budget_chf: 12 }) });
    expect(wrapper.find("[data-test=budget-saved]").exists()).toBe(true);
  });

  it("exploitant : la rubrique Plateforme", async () => {
    await as(true);
    mockGet(false);
    const { wrapper } = await mountSettings("plateforme");
    expect(wrapper.find("[data-test=toc-plateforme]").exists()).toBe(true);
    expect(wrapper.find("[data-test=budget-form]").exists()).toBe(false);
  });
});

describe("SettingsView, le bon rythme (docs/86)", () => {
  it("les jours de recherche et l'heure du message des offres", async () => {
    mockGet(false);
    const { wrapper } = await mountSettings("rythme");
    const form = wrapper.find("[data-test=rhythm-form]");
    expect((form.find("[data-test=rhythm-day-0]").element as HTMLInputElement).checked).toBe(true);
    expect((form.find("[data-test=rhythm-day-5]").element as HTMLInputElement).checked).toBe(false);
    await form.find("[data-test=rhythm-day-2]").setValue(false);
    await form.find("[data-test=rhythm-hour]").setValue("8");
    const PUT = vi.mocked((await import("../api/client")).api.PUT).mockResolvedValue({ data: null } as never);
    await form.trigger("submit");
    await flushPromises();
    const body = (PUT.mock.calls.at(-1) as unknown as [string, { body: Record<string, unknown> }])[1].body;
    expect(body.rhythm_days).toEqual([0, 1, 3, 4]);
    expect(body.offers_notify_hour).toBe(8);
    expect(body.offers_notify_mode).toBe("daily");
    // Une pause, puis la terminer.
    await form.find("[data-test=pause-from]").setValue("2026-10-26");
    await form.find("[data-test=pause-until]").setValue("2026-11-01");
    await form.trigger("submit");
    await flushPromises();
    const paused = (PUT.mock.calls.at(-1) as unknown as [string, { body: Record<string, unknown> }])[1].body;
    expect([paused.rhythm_pause_from, paused.rhythm_pause_until]).toEqual(["2026-10-26", "2026-11-01"]);
    await form.find("[data-test=pause-end]").trigger("click");
    await flushPromises();
    const ended = (PUT.mock.calls.at(-1) as unknown as [string, { body: Record<string, unknown> }])[1].body;
    expect(ended.rhythm_pause_from).toBeNull();
    // « Dès qu'elles arrivent » : l'heure ne sert plus.
    await form.find("[data-test=rhythm-instant]").setValue(true);
    expect(form.find("[data-test=rhythm-hour]").attributes("disabled")).toBeDefined();
  });
});


describe("Des Réglages épurés (docs/106)", () => {
  it("une rubrique, une carte ; le seuil en pastilles, enregistré au clic", async () => {
    mockGet(true);
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: { notify_score_threshold: 80 } } as never);
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.findAll("[data-test=settings-card]")).toHaveLength(1);
    const choices = wrapper.findAll("[data-test=notify-form] [role=radio]").map((b) => b.text());
    expect(choices).toEqual(["50", "60", "70", "80", "90"]);
    expect(wrapper.find("[data-test=threshold-70]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=save-notify]").exists()).toBe(false);
    await wrapper.find("[data-test=threshold-80]").trigger("click");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", { body: expect.objectContaining({ notify_score_threshold: 80 }) });
    expect(wrapper.find("[data-test=threshold-saved]").text()).toBe("Enregistré");
    // La notification de test : une ligne, son nom à gauche, « Envoyer » à droite.
    expect(wrapper.find("[data-test=test-notification]").text()).toBe("Envoyer");
    expect(wrapper.find("[data-test=notifications] legend").text()).toBe("Téléphone");
  });

  it("un seuil d'avant, hors des cinq, reste proposé", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data: path === "/api/notifications" ? { configured: false } : { notify_score_threshold: 75, llm_monthly_budget_chf: 10 },
      }),
    );
    const { wrapper } = await mountSettings("notifications");
    const choices = wrapper.findAll("[data-test=notify-form] [role=radio]").map((b) => b.text());
    expect(choices).toEqual(["50", "60", "70", "75", "80", "90"]);
  });

  it("« Enregistrer » plein pour un formulaire de plusieurs champs", async () => {
    mockGet(false);
    const { wrapper } = await mountSettings();
    expect(wrapper.find("[data-test=save-settings]").classes()).toContain("primary");
  });
});
