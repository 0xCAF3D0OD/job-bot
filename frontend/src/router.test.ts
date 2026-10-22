import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "./composables/useAuth";

const GET = vi.fn();
vi.mock("./api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn(), use: vi.fn() } }));
afterEach(() => {
  vi.resetAllMocks();
  useAuth().me.value = null;
});

describe("routes réservées (docs/18 §1)", () => {
  it("sans connexion : la présentation de la plateforme, le reste mène à la connexion", async () => {
    GET.mockResolvedValue({ data: { authenticated: false, username: null, setup_needed: false, auth_enabled: true } });
    const { router } = await import("./router");
    await router.push("/la-plateforme");
    expect(router.currentRoute.value.name).toBe("discover");
    // Les Actualités demandent la connexion depuis la 0.55.0 (docs/67).
    await router.push("/actualites");
    expect(router.currentRoute.value.name).toBe("login");
    // Ancienne adresse : redirigée vers l'onglet, puis vers la connexion.
    await router.push("/candidatures?vue=orp&mois=2026-09");
    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.suite).toBe("/candidatures/suivi?mois=2026-09");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("login");
  });

  it("connecté : la page de connexion renvoie vers l'application", async () => {
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
    const { router } = await import("./router");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("trainings");
    // Le Bilan (docs/126 §1) : les anciennes adresses, Progresser compris, mènent au bon onglet,
    // avec leurs paramètres.
    await router.push("/formations?onglet=miennes");
    expect(router.currentRoute.value.fullPath).toBe("/bilan/formations?onglet=miennes");
    await router.push("/actualites?rubrique=videos");
    expect(router.currentRoute.value.fullPath).toBe("/bilan/actualites?rubrique=videos");
    await router.push("/progresser/formations?onglet=miennes");
    expect(router.currentRoute.value.fullPath).toBe("/bilan/formations?onglet=miennes");
    await router.push("/progresser");
    expect(router.currentRoute.value.path).toBe("/bilan/actualites");
    await router.push("/candidatures/bilan?mois=2026-10");
    expect(router.currentRoute.value.fullPath).toBe("/bilan?mois=2026-10");
    expect(router.currentRoute.value.name).toBe("insights");
    await router.push("/connexion?suite=/offres");
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/offres");
    // Rubrique Candidatures (docs/19 §2) : /candidatures ouvre les Offres, anciens liens redirigés.
    await router.push("/candidatures");
    expect(router.currentRoute.value.name).toBe("offers");
    await router.push("/orp?mois=2026-09");
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/suivi?mois=2026-09");
    await router.push("/offres/12/preparer");
    expect(router.currentRoute.value.name).toBe("preparation");
    await router.push("/candidatures?mois=2026-08");
    expect(router.currentRoute.value.fullPath).toBe("/candidatures/suivi?mois=2026-08");
    // Journal des recherches devenu l'onglet Alertes (docs/20 §1).
    await router.push("/journal");
    expect(router.currentRoute.value.name).toBe("alerts");
    await router.push("/candidatures/journal");
    expect(router.currentRoute.value.name).toBe("alerts");
    // État technique devenu la page Diagnostic (docs/21 §6), à l'exploitant seulement
    // (docs/108 §3) : un invité revient aux Réglages.
    await router.push("/etat");
    expect(router.currentRoute.value.path).toBe("/reglages");
    useAuth().me.value = { ...useAuth().me.value!, is_owner: true };
    await router.push("/etat");
    expect(router.currentRoute.value.name).toBe("diagnostic");
  });
});

describe("accueil d'un nouveau compte (docs/66 §4)", () => {
  it("à faire : chaque page mène à l'accueil ; remis à plus tard : on circule", async () => {
    useAuth().me.value = {
      authenticated: true,
      username: "camille",
      setup_needed: false,
      auth_enabled: true,
      is_owner: false,
      welcome: "pending",
      demo: false,
    };
    const { router } = await import("./router");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("welcome");
    await router.push("/tes-donnees");
    expect(router.currentRoute.value.name).toBe("privacy");
    useAuth().me.value = { ...useAuth().me.value!, welcome: "postponed" };
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("trainings");
  });
});

describe("demander un compte (docs/102)", () => {
  it("ouvert sans connexion ; connecté, renvoie vers l'application", async () => {
    GET.mockResolvedValue({ data: { authenticated: false, username: null, setup_needed: false, auth_enabled: true } });
    const { router } = await import("./router");
    await router.push("/inscription");
    expect(router.currentRoute.value.name).toBe("signup");
    await router.push("/la-plateforme");
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
    await router.push("/inscription");
    expect(router.currentRoute.value.fullPath).toBe("/aujourdhui");
  });
});
