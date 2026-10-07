import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "./composables/useAuth";

const GET = vi.fn();
vi.mock("./api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn(), use: vi.fn() } }));
afterEach(() => {
  vi.resetAllMocks();
  useAuth().me.value = null;
});

describe("routes réservées (docs/18 §1)", () => {
  it("sans connexion : Actualités ouvertes, le reste mène à la connexion", async () => {
    GET.mockResolvedValue({ data: { authenticated: false, username: null, setup_needed: false, auth_enabled: true } });
    const { router } = await import("./router");
    await router.push("/actualites");
    expect(router.currentRoute.value.name).toBe("news");
    // Ancienne adresse : redirigée vers l'onglet, puis vers la connexion.
    await router.push("/candidatures?vue=orp&mois=2026-09");
    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.suite).toBe("/candidatures/suivi?mois=2026-09");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("login");
  });

  it("connecté : la page de connexion renvoie vers l'application", async () => {
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true };
    const { router } = await import("./router");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("trainings");
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
    // État technique devenu la page Diagnostic (docs/21 §6).
    await router.push("/etat");
    expect(router.currentRoute.value.name).toBe("diagnostic");
  });
});
