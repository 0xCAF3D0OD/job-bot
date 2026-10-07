import { afterEach, describe, expect, it, vi } from "vitest";

import { api, PROFILE_HEADER, PROFILE_KEY, UNAUTHORIZED_EVENT } from "./client";

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe("en-tête du profil d'essai", () => {
  it("envoie le profil choisi, rien pour le principal", async () => {
    const fetch = vi.fn(() => Promise.resolve(new Response("{}", { headers: { "Content-Type": "application/json" } })));
    vi.stubGlobal("fetch", fetch);
    await api.GET("/api/profiles", { fetch });
    expect((fetch.mock.calls[0] as unknown as [Request])[0].headers.get(PROFILE_HEADER)).toBeNull();
    localStorage.setItem(PROFILE_KEY, "7");
    await api.GET("/api/profiles", { fetch });
    expect((fetch.mock.calls[1] as unknown as [Request])[0].headers.get(PROFILE_HEADER)).toBe("7");
  });
});

describe("session expirée", () => {
  it("un 401 hors /api/auth prévient l'application", async () => {
    const listener = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, listener);
    const answer = (status: number) => () => Promise.resolve(new Response("{}", { status, headers: { "Content-Type": "application/json" } }));
    await api.GET("/api/orp", { fetch: vi.fn(answer(401)) });
    expect(listener).toHaveBeenCalledTimes(1);
    await api.GET("/api/auth/me", { fetch: vi.fn(answer(401)) });
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(UNAUTHORIZED_EVENT, listener);
  });
});
