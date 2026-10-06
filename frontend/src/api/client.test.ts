import { afterEach, describe, expect, it, vi } from "vitest";

import { api, PROFILE_HEADER, PROFILE_KEY } from "./client";

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
