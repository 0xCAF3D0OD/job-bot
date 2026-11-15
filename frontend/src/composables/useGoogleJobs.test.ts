import { describe, expect, it, vi } from "vitest";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) } }));

import { googleJobsPill, hideGoogleJobs, loadGoogleJobs } from "./useGoogleJobs";

const url = "https://www.google.com/search?q=Comptable+emploi+Sion&udm=8";

describe("Google Emplois en attendant les offres (docs/144, accord de Kevin du 15.11)", () => {
  it("la pastille donne le métier et le lieu s'il y en a un, sans promesse de date", () => {
    expect(googleJobsPill({ terms: "Comptable", location: "Sion", url })).toBe("Comptable · Sion");
    expect(googleJobsPill({ terms: "Comptable", location: null, url })).toBe("Comptable");
  });

  it("Candidatures vide : le lien vient du serveur ; rien sans réponse ou hors ligne", async () => {
    GET.mockResolvedValueOnce({ data: { terms: "Comptable", location: "Sion", url } });
    expect(await loadGoogleJobs()).toEqual({ terms: "Comptable", location: "Sion", url });
    expect(GET).toHaveBeenCalledWith("/api/google-jobs");
    GET.mockResolvedValueOnce({ data: null });
    expect(await loadGoogleJobs()).toBeNull();
    GET.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    expect(await loadGoogleJobs()).toBeNull();
  });

  it("« Masquer » est retenu côté serveur", async () => {
    PUT.mockResolvedValueOnce({ response: { ok: true } });
    expect(await hideGoogleJobs()).toBe(true);
    expect(PUT).toHaveBeenCalledWith("/api/google-jobs", { body: { hidden: true }, keepalive: false });
  });
});
