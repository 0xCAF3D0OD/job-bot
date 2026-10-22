// Corrections de l'audit d'ergonomie du 22.10.2026 (0.99.1).
import { afterEach, describe, expect, it, vi } from "vitest";

import { pageTitle } from "./router";

const GET = vi.fn();
vi.mock("./api/client", async (original) => ({ ...(await original<object>()), api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

describe("audit du 22.10.2026", () => {
  it("chaque page a son titre d'onglet, « Page · jobA1 »", () => {
    expect(pageTitle("offers")).toBe("Offres · jobA1");
    expect(pageTitle("orp-meeting")).toBe("Rendez-vous ORP · jobA1");
    expect(pageTitle("terms")).toBe("Conditions d'utilisation · jobA1");
    expect(pageTitle(undefined)).toBe("jobA1");
  });

  it("une candidature retenue dont l'offre n'existe plus est oubliée", async () => {
    localStorage.setItem("jobbot-candidatures", "/candidatures/offres/1109/preparer");
    vi.resetModules();
    const { useJobsMemory } = await import("./composables/useJobsMemory");
    GET.mockResolvedValue({ response: { status: 404 } });
    const memory = useJobsMemory();
    expect(memory.last.value).toBe("/candidatures/offres/1109/preparer");
    await memory.check();
    expect(memory.last.value).toBe("/candidatures/offres");
    memory.remember("/candidatures/offres/12/preparer?doc=cv");
    memory.forget("/candidatures/offres/12/preparer");
    expect(memory.last.value).toBe("/candidatures/offres");
  });
});
