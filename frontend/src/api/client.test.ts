import { afterEach, describe, expect, it, vi } from "vitest";

import { api, DEMO_REFUSED_EVENT, MAINTENANCE_EVENT, MAINTENANCE_READ_EVENT, PROFILE_HEADER, PROFILE_KEY, UNAUTHORIZED_EVENT } from "./client";

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

// Réponse simulée, passée à la requête (le client garde le fetch de son démarrage).
function respond(status: number, body: unknown): { fetch: typeof fetch } {
  return { fetch: async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }) };
}

describe("démo publique (docs/72)", () => {
  it("annonce une écriture refusée par la démo, avec son message", async () => {
    const heard: string[] = [];
    const listener = (event: Event) => heard.push(String((event as CustomEvent<string>).detail));
    window.addEventListener(DEMO_REFUSED_EVENT, listener);
    const { response, error } = await api.PUT("/api/applications/{application_id}/job-room", {
      params: { path: { application_id: 1 } },
      ...respond(403, { detail: "Dans la démo, rien n'est enregistré.", demo: true }),
    });
    expect(response.status).toBe(403);
    // La réponse reste lisible par la page qui a fait la demande.
    expect(error).toEqual({ detail: "Dans la démo, rien n'est enregistré.", demo: true });
    // Un autre refus (droits, connexion) n'est pas pris pour la démo.
    await api.PUT("/api/applications/{application_id}/job-room", {
      params: { path: { application_id: 1 } },
      ...respond(403, { detail: "réservé à l'exploitant" }),
    });
    window.removeEventListener(DEMO_REFUSED_EVENT, listener);
    expect(heard).toEqual(["Dans la démo, rien n'est enregistré."]);
  });
});

describe("maintenance (docs/79)", () => {
  it("la page d'attente pour une maintenance, un serveur qui ne répond pas, pas pour une autre erreur", async () => {
    const heard: (string | null)[] = [];
    const listener = (event: Event) => heard.push((event as CustomEvent<string | null>).detail);
    window.addEventListener(MAINTENANCE_EVENT, listener);
    await api.GET("/api/orp", respond(503, { detail: "…", maintenance: true, message: "Dix minutes" }));
    // L'intermédiaire (Vite, Caddy) quand l'API redémarre : 502, sans corps JSON.
    await api.GET("/api/orp", { fetch: async () => new Response("", { status: 502 }) });
    await expect(api.GET("/api/orp", { fetch: () => Promise.reject(new TypeError("Failed to fetch")) })).rejects.toThrow();
    // Une IA indisponible (503 de la route), une requête annulée : pas de maintenance.
    await api.GET("/api/orp", respond(503, { detail: "IA momentanément indisponible, réessayer" }));
    await expect(
      api.GET("/api/orp", { fetch: () => Promise.reject(new DOMException("annulée", "AbortError")) }),
    ).rejects.toThrow();
    window.removeEventListener(MAINTENANCE_EVENT, listener);
    expect(heard).toEqual(["Dix minutes", null, null]);
  });
});

describe("maintenance en lecture seule (docs/80)", () => {
  it("une écriture refusée prévient sans poser la page d'attente", async () => {
    const waiting = vi.fn();
    const read: (string | null)[] = [];
    const listener = (event: Event) => read.push((event as CustomEvent<string | null>).detail);
    window.addEventListener(MAINTENANCE_EVENT, waiting);
    window.addEventListener(MAINTENANCE_READ_EVENT, listener);
    await api.POST("/api/news/seen", respond(503, { detail: "…", maintenance: true, mode: "lecture", message: "Sauvegarde" }));
    window.removeEventListener(MAINTENANCE_EVENT, waiting);
    window.removeEventListener(MAINTENANCE_READ_EVENT, listener);
    expect(read).toEqual(["Sauvegarde"]);
    expect(waiting).not.toHaveBeenCalled();
  });
});
