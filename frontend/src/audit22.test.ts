// Corrections de l'audit d'ergonomie du 22.10.2026 (0.99.1).
import { afterEach, describe, expect, it, vi } from "vitest";

import { pageTitle } from "./router";

const GET = vi.fn();
vi.mock("./api/client", async (original) => ({ ...(await original<object>()), api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

describe("audit du 22.10.2026", () => {
  it("chaque page a son titre d’onglet, « Page · jobA1 »", () => {
    expect(pageTitle("offers")).toBe("Offres · jobA1");
    expect(pageTitle("orp-meeting")).toBe("Rendez-vous ORP · jobA1");
    expect(pageTitle("terms")).toBe("Conditions d’utilisation · jobA1");
    expect(pageTitle(undefined)).toBe("jobA1");
  });

  it("une préparation retenue avant le 13.11.2026 n’est plus reprise : le menu mène aux offres", async () => {
    localStorage.setItem("jobbot-candidatures", "/candidatures/offres/1109/preparer");
    vi.resetModules();
    const { useJobsMemory } = await import("./composables/useJobsMemory");
    expect(useJobsMemory().last.value).toBe("/candidatures/offres");
  });
});
