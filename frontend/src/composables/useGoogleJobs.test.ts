import { describe, expect, it, vi } from "vitest";

const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { PUT: (...a: unknown[]) => PUT(...a) } }));

import { googleJobsPill, hideGoogleJobs } from "./useGoogleJobs";

const url = "https://www.google.com/search?q=Comptable+emploi+Sion&udm=8";

describe("Google Emplois en attendant les offres (docs/144, accord de Kevin du 15.11)", () => {
  it("la pastille donne le métier et le lieu s'il y en a un, sans promesse de date", () => {
    expect(googleJobsPill({ terms: "Comptable", location: "Sion", url })).toBe("Comptable · Sion");
    expect(googleJobsPill({ terms: "Comptable", location: null, url })).toBe("Comptable");
  });

  it("« Masquer » est retenu côté serveur", async () => {
    PUT.mockResolvedValueOnce({ response: { ok: true } });
    expect(await hideGoogleJobs()).toBe(true);
    expect(PUT).toHaveBeenCalledWith("/api/google-jobs", { body: { hidden: true }, keepalive: false });
  });
});
