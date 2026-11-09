import { afterEach, describe, expect, it, vi } from "vitest";

const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: vi.fn(), POST: (path: string) => POST(path) } }));

import { LOGIN_PATH, leave, useAuth } from "./useAuth";

// Incident du 2026-11-09 : après « Se déconnecter », le Suivi ORP restait affiché avec les candidatures, parce
// que la page ne changeait pas (route inexistante) et que rien ne vidait la mémoire de l'application.
describe("Déconnexion : rien du compte ne reste à l'écran ni en mémoire", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    POST.mockReset();
  });

  it("ferme la session, oublie le compte et recharge la page sur la connexion", async () => {
    POST.mockResolvedValue({ response: { ok: true } });
    const to = vi.spyOn(leave, "to").mockImplementation(() => undefined);
    const { me, loggedIn, logout } = useAuth();
    me.value = { authenticated: true, username: "kevin", setup_needed: false, auth_enabled: true, is_owner: true, welcome: "done", demo: false };

    await logout();

    expect(POST).toHaveBeenCalledWith("/api/auth/logout");
    expect(loggedIn.value).toBe(false);
    expect(me.value?.username).toBeNull();
    expect(to).toHaveBeenCalledWith(LOGIN_PATH);
  });

  it("« Se déconnecter partout » fait de même", async () => {
    POST.mockResolvedValue({ response: { ok: true } });
    const to = vi.spyOn(leave, "to").mockImplementation(() => undefined);
    await useAuth().logout(true);
    expect(POST).toHaveBeenCalledWith("/api/auth/logout-all");
    expect(to).toHaveBeenCalledWith(LOGIN_PATH);
  });

  it("quitte la page même quand l'appel échoue (réseau coupé)", async () => {
    POST.mockRejectedValue(new TypeError("Failed to fetch"));
    const to = vi.spyOn(leave, "to").mockImplementation(() => undefined);
    const { me, loggedIn, logout } = useAuth();
    me.value = { authenticated: true, username: "kevin", setup_needed: false, auth_enabled: true, is_owner: true, welcome: "done", demo: false };

    await expect(logout()).rejects.toThrow();

    expect(loggedIn.value).toBe(false);
    expect(to).toHaveBeenCalledWith(LOGIN_PATH);
  });
});
