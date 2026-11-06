import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { createMemoryHistory, createRouter } from "vue-router";

import SettingsView from "./SettingsView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PUT: vi.fn() },
}));
// Démonter avant de remettre les maquettes à zéro : sinon, au test suivant, `as(true)` fait
// apparaître ProfilesPanel dans la page restée montée, qui appelle un GET déjà vidé.
enableAutoUnmount(afterEach);
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
    expect(wrapper.find("[data-test=notifications]").text()).toContain("Pas encore disponibles sur cette plateforme");
    expect(wrapper.find("[data-test=test-notification]").exists()).toBe(false);
  });

  it("configurées : envoie une notification de test", async () => {
    mockGet(true);
    POST.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountSettings("notifications");
    await wrapper.find("[data-test=test-notification]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/notifications/test");
    expect(wrapper.find("[data-test=notifications] span.muted[role=status]").text()).toContain("Notification envoyée");
  });
});

describe("SettingsView, la page Réglages unique du téléphone (maquette Réglages, Kevin, 6.11)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("Notifications, Affichage et Mes données à la suite ; quatre interrupteurs, le seuil sous Nouvelles offres", async () => {
    vi.stubGlobal("matchMedia", (media: string) => ({ matches: media.includes("820px"), addEventListener() {}, removeEventListener() {} }));
    mockGet(false);
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: { notify_follow_ups: false } } as never);
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.findAll(".settings-section > .section-title").map((h) => h.text())).toEqual(["Notifications", "Affichage", "Mes données"]);
    const rows = wrapper.findAll("[data-test=notify-switches] .setting-row-title").map((t) => t.text());
    expect(rows).toEqual(["Nouvelles offres", "M'avertir dès", "Relances", "Objectif ORP", "Actualités et formations"]);
    expect(wrapper.findAll("[data-test=notify-switches] input[role=switch]").map((i) => (i.element as HTMLInputElement).checked)).toEqual([true, true, true, false]);
    expect(wrapper.find("[data-test=notify-form]").exists()).toBe(false);
    await wrapper.find("[data-test=switch-notify_follow_ups]").trigger("change");
    await flushPromises();
    expect(put.mock.calls.at(-1)?.[1]).toMatchObject({ body: { notify_follow_ups: false } });
    // Sur ordinateur, une rubrique par page, comme avant.
    vi.unstubAllGlobals();
    const desktop = (await mountSettings("notifications")).wrapper;
    expect(desktop.find("[data-test=notify-switches]").exists()).toBe(false);
    expect(desktop.find("[data-test=section-affichage]").exists()).toBe(false);
  });
});

describe("SettingsView, enregistrement réglage par réglage (1.6.66)", () => {
  function settings(extra: Record<string, unknown> = {}) {
    return { orp_monthly_target: 20, notify_score_threshold: 70, llm_monthly_budget_chf: 10, orp_due_day: 5, ...extra };
  }
  function serveSettings() {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/notifications" ? { configured: false, server: "https://ntfy.sh" } : settings() }),
    );
  }

  it("un champ chiffré s'enregistre quand on le quitte, pas à chaque frappe ; « Enregistré » sur la ligne", async () => {
    serveSettings();
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: settings({ orp_due_day: 10 }) } as never);
    const { wrapper } = await mountSettings();
    const input = wrapper.find("[data-test=due-day]");
    // La frappe seule (événement input) n'enregistre rien.
    (input.element as HTMLInputElement).value = "10";
    await input.trigger("input");
    await flushPromises();
    expect(put).not.toHaveBeenCalled();
    await input.trigger("change");
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
    const row = input.element.closest("[data-test=setting-row]")!;
    expect(row.querySelector("[data-test=setting-saved]")!.textContent).toContain("Enregistré");
    // Plus de bouton « Enregistrer » nulle part.
    expect(wrapper.text()).not.toContain("Enregistrer");
  });

  it("une valeur impossible : l'erreur sous le champ, l'ancienne reste enregistrée, la saisie reste", async () => {
    serveSettings();
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT);
    const { wrapper } = await mountSettings();
    const input = wrapper.find("[data-test=due-day]");
    await input.setValue(31);
    await input.trigger("change");
    await flushPromises();
    expect(put).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=setting-error]").text()).toBe("Entre 2 et 28. Le 5 reste enregistré.");
    expect(input.attributes("aria-invalid")).toBe("true");
    expect((input.element as HTMLInputElement).value).toBe("31");
  });
});

describe("SettingsView, une rubrique par page (étape 10b, C10)", () => {
  it("une seule rubrique affichée, son nom en titre, « Retour au compte »", async () => {
    mockGet(false);
    const { wrapper, router } = await mountSettings();
    // Sans rubrique valable, la première : Objectif ORP et sites.
    expect(wrapper.find("h1").text()).toBe("Objectif ORP et sites");
    const back = wrapper.find("[data-test=settings-back]");
    expect(back.text()).toContain("Retour au compte");
    expect(back.attributes("href")).toBe("/compte");
    expect(wrapper.find("[data-test=settings-list]").exists()).toBe(false);
    expect(wrapper.find("[data-test=due-day]").exists()).toBe(true);
    expect(wrapper.find("[data-test=notifications]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("M'avertir d'une offre");
    await router.push({ query: { rubrique: "notifications" } });
    await flushPromises();
    expect(wrapper.find("h1").text()).toBe("Notifications");
    expect(wrapper.text()).toContain("M'avertir d'une offre dès");
    expect(wrapper.find("[data-test=due-day]").exists()).toBe(false);
    expect(wrapper.find("[data-test=section-rythme]").exists()).toBe(false);
    // « Chercher l'annonce chez l'employeur » n'est plus ici (1.6.28).
    expect(wrapper.find("[data-test=employer-threshold]").exists()).toBe(false);
  });

  it("l'ancienne rubrique Compte se partage entre Affichage, Formule et Mes données", async () => {
    mockGet(false);
    const rubrics: [string, string][] = [
      ["affichage", "Affichage"],
      ["formule", "Formule"],
      ["donnees", "Mes données"],
    ];
    for (const [rubrique, title] of rubrics) {
      const { wrapper } = await mountSettings(rubrique);
      expect(wrapper.find("h1").text(), rubrique).toBe(title);
      expect(wrapper.find(`[data-test=section-${rubrique}]`).exists(), rubrique).toBe(true);
      wrapper.unmount();
    }
  });

  it("« Chercher l'annonce chez l'employeur » est dans Recherche d'emploi (1.6.28)", async () => {
    mockGet(false);
    const { wrapper } = await mountSettings("recherche");
    const employer = wrapper.find("[data-test=employer-threshold]");
    expect(employer.exists()).toBe(true);
    expect(employer.element.closest("[data-test=setting-row]")!.textContent).toContain("Chercher l'annonce chez l'employeur");
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

  it("Mes données : des cartes de réglages, « Se déconnecter partout » à droite de sa ligne (1.6.67)", async () => {
    await as(false);
    mockGet(false);
    const { wrapper } = await mountSettings("donnees");
    expect(wrapper.find("[data-test=settings-card] fieldset").exists()).toBe(false);
    const titles = wrapper.findAll("[data-test=settings-card] .setting-row-title").map((t) => t.text());
    expect(titles.filter((t) => t === "Connexion")).toHaveLength(1);
    const logout = wrapper.find("[data-test=logout-all]");
    expect(logout.element.closest(".setting-row-control")).not.toBeNull();
    expect(logout.classes()).toContain("secondary");
  });

  it("compte invité : la formule plutôt qu'un plafond en francs, ni Plateforme ni profils d'essai", async () => {
    await as(false);
    mockGet(false);
    const { wrapper } = await mountSettings("ia");
    // Des nombres, pas des francs (docs/125 §2) : la rubrique renvoie à la formule.
    const fixed = wrapper.find("[data-test=budget-fixed]");
    expect(fixed.text()).toContain("Formule Essentiel");
    expect(fixed.text()).not.toContain("CHF");
    expect(fixed.find("[data-test=see-plan]").attributes("href")).toContain("rubrique=formule");
    expect(wrapper.find("[data-test=budget-form]").exists()).toBe(false);
    const platform = await mountSettings("plateforme");
    expect(platform.wrapper.find("[data-test=section-plateforme]").exists()).toBe(false);
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
    await wrapper.find("[data-test=phone-switch]").trigger("change");
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
    const input = wrapper.find("[data-test=budget]");
    await input.setValue(12);
    await input.trigger("change");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", { body: expect.objectContaining({ llm_monthly_budget_chf: 12 }) });
    expect(wrapper.find("[data-test=budget-form] [data-test=setting-saved]").text()).toContain("Enregistré");
  });

  it("exploitant : la rubrique Plateforme", async () => {
    await as(true);
    mockGet(false);
    const { wrapper } = await mountSettings("plateforme");
    expect(wrapper.find("h1").text()).toBe("Administration");
    expect(wrapper.find("[data-test=section-plateforme]").exists()).toBe(true);
    expect(wrapper.find("[data-test=budget-form]").exists()).toBe(false);
  });
});

describe("SettingsView, le bon rythme (docs/86)", () => {
  it("les jours, la pause et le message des offres s'appliquent tout de suite", async () => {
    mockGet(false);
    const PUT = vi.mocked((await import("../api/client")).api.PUT).mockResolvedValue({ data: null } as never);
    const { wrapper } = await mountSettings("rythme");
    const last = () => (PUT.mock.calls.at(-1) as unknown as [string, { body: Record<string, unknown> }])[1].body;
    expect((wrapper.find("[data-test=rhythm-day-0]").element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find("[data-test=rhythm-day-5]").element as HTMLInputElement).checked).toBe(false);
    await wrapper.find("[data-test=rhythm-day-2]").setValue(false);
    await flushPromises();
    expect(last().rhythm_days).toEqual([0, 1, 3, 4]);
    await wrapper.find("[data-test=rhythm-hour]").setValue("8");
    await flushPromises();
    expect(last().offers_notify_hour).toBe(8);
    expect(last().offers_notify_mode).toBe("daily");
    // Une pause, puis la terminer.
    await wrapper.find("[data-test=pause-from]").setValue("2026-10-26");
    await wrapper.find("[data-test=pause-until]").setValue("2026-11-01");
    await flushPromises();
    expect([last().rhythm_pause_from, last().rhythm_pause_until]).toEqual(["2026-10-26", "2026-11-01"]);
    await wrapper.find("[data-test=pause-end]").trigger("click");
    await flushPromises();
    expect(last().rhythm_pause_from).toBeNull();
    // « Dès qu'elles arrivent » : l'heure ne sert plus.
    await wrapper.find("[data-test=rhythm-instant]").setValue(true);
    await flushPromises();
    expect(last().offers_notify_mode).toBe("instant");
    expect(wrapper.find("[data-test=rhythm-hour]").attributes("disabled")).toBeDefined();
  });
});

describe("Des Réglages épurés (docs/106)", () => {
  it("une rubrique, une carte ; le seuil en mots, enregistré au clic (C11)", async () => {
    mockGet(true);
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: { notify_score_threshold: 85 } } as never);
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.findAll("[data-test=settings-card]")).toHaveLength(1);
    const choices = wrapper.findAll("[data-test=notify-form] [role=radio]").map((b) => b.text());
    expect(choices).toEqual(["Très proche", "Proche", "À creuser"]);
    expect(wrapper.find("[data-test=threshold-75]").attributes("aria-checked")).toBe("true");

    await wrapper.find("[data-test=threshold-85]").trigger("click");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/settings", { body: expect.objectContaining({ notify_score_threshold: 85 }) });
    expect(wrapper.find("[data-test=notify-form] [data-test=setting-saved]").text()).toContain("Enregistré");
    // La notification de test : une ligne, son nom à gauche, « Envoyer » à droite.
    expect(wrapper.find("[data-test=test-notification] .busy-label").text()).toBe("Envoyer");
    // L'interrupteur du téléphone n'est que pour un compte invité ; ici, la ligne de test seule.
    expect(wrapper.find("[data-test=notifications] .setting-row-title").text()).toBe("Notification de test");
  });

  it("un seuil d'avant tombe sur le mot qui le contient", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data: path === "/api/notifications" ? { configured: false } : { notify_score_threshold: 72, llm_monthly_budget_chf: 10 },
      }),
    );
    const { wrapper } = await mountSettings("notifications");
    expect(wrapper.find("[data-test=threshold-75]").attributes("aria-checked")).toBe("true");
  });
});
