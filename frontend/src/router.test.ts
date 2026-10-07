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
    await router.push("/candidatures?vue=orp");
    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.suite).toBe("/candidatures?vue=orp");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("login");
  });

  it("connecté : la page de connexion renvoie vers l'application", async () => {
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true };
    const { router } = await import("./router");
    await router.push("/formations");
    expect(router.currentRoute.value.name).toBe("trainings");
    await router.push("/connexion?suite=/offres");
    expect(router.currentRoute.value.fullPath).toBe("/offres");
  });
});
