// Démo publique (docs/72) : une écriture refusée par la démo est annoncée à l'application.
import { afterEach, describe, expect, it, vi } from "vitest";

import { api, DEMO_REFUSED_EVENT } from "./client";

afterEach(() => vi.restoreAllMocks());

// Réponse simulée, passée à la requête (le client garde le fetch de son démarrage).
function answer(status: number, body: unknown): { fetch: typeof fetch } {
  return { fetch: async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }) };
}

describe("client de l'API", () => {
  it("annonce une écriture refusée par la démo, avec son message", async () => {
    const heard: string[] = [];
    const listener = (event: Event) => heard.push(String((event as CustomEvent<string>).detail));
    window.addEventListener(DEMO_REFUSED_EVENT, listener);
    const { response, error } = await api.PUT("/api/applications/{application_id}/job-room", {
      params: { path: { application_id: 1 } },
      ...answer(403, { detail: "Dans la démo, rien n'est enregistré.", demo: true }),
    });
    expect(response.status).toBe(403);
    // La réponse reste lisible par la page qui a fait la demande.
    expect(error).toEqual({ detail: "Dans la démo, rien n'est enregistré.", demo: true });
    // Un autre refus (droits, connexion) n'est pas pris pour la démo.
    await api.PUT("/api/applications/{application_id}/job-room", {
      params: { path: { application_id: 1 } },
      ...answer(403, { detail: "réservé à l'exploitant" }),
    });
    window.removeEventListener(DEMO_REFUSED_EVENT, listener);
    expect(heard).toEqual(["Dans la démo, rien n'est enregistré."]);
  });
});
