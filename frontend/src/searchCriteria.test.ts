import { afterEach, describe, expect, it, vi } from "vitest";

import { combinations, loadSearchCriteria, rateLabel, saveSearchCriteria } from "./searchCriteria";

const GET = vi.fn();
const PUT = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("./api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const cell = (site: string, status = "todo") => ({ site, url: `https://${site}.example`, status, received_at: null, created_at: null });
const search = (id: number, terms: string, location: string | null, cells = [cell("jobup")]) => ({ id, terms, location, active: true, cells });
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const page = (searches: ReturnType<typeof search>[]): any => ({
  mailbox: "moi@exemple.ch",
  sites: [{ slug: "jobup", name: "jobup" }, { slug: "linkedin", name: "LinkedIn" }],
  searches,
});
const criteria = { locations: ["Lausanne"], min_rate: 80, keywords: [] };
function serve(roles: string[], locations = criteria.locations) {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/criteria" ? { data: { criteria: { ...criteria, locations } } } : { data: { roles } }),
  );
  PUT.mockImplementation((path: string, { body }: { body: unknown }) => Promise.resolve({ data: path === "/api/criteria" ? { criteria: body } : body }));
}

describe("« Ta recherche », une seule source : les critères du Profil (Kevin, 17.11)", () => {
  it("chaque poste avec chaque lieu ; aucun lieu = une recherche par poste, sans lieu ; cantons écrits en entier", () => {
    expect(combinations({ roles: ["DevOps", "SRE"], places: ["Lausanne", "VD"] })).toEqual([
      { terms: "DevOps", location: "Lausanne" },
      { terms: "DevOps", location: "Vaud" },
      { terms: "SRE", location: "Lausanne" },
      { terms: "SRE", location: "Vaud" },
    ]);
    expect(combinations({ roles: ["DevOps", "devops "], places: [] })).toEqual([{ terms: "DevOps", location: null }]);
  });

  it("les 7 taux : Tous, Dès 50 % … Dès 90 %, 100 %", () => {
    expect([null, 50, 90, 100].map(rateLabel)).toEqual(["Tous", "Dès 50 %", "Dès 90 %", "100 %"]);
  });

  it("le volet reprend les critères et les recherches actives qui n'y sont pas encore", async () => {
    serve(["DevOps"], ["VD"]);
    const loaded = await loadSearchCriteria(page([search(1, "DevOps", "Vaud"), search(2, "SRE", "Genève")]));
    expect(loaded).toEqual({ roles: ["DevOps", "SRE"], places: ["VD", "Genève"], rate: 80 });
  });

  it("enregistrer : les critères, puis les recherches retirées supprimées, celles qui manquent créées", async () => {
    serve(["DevOps", "SRE"]);
    DELETE.mockResolvedValue({ data: page([]) });
    POST.mockResolvedValue({ data: page([]) });
    const current = page([
      search(1, "DevOps", "Lausanne"),
      search(2, "SRE", "Lausanne", [cell("jobup", "created"), cell("linkedin", "received"), cell("indeed")]),
    ]);
    const saved = await saveSearchCriteria({ roles: ["DevOps"], places: ["Lausanne", "GE"], rate: 100 }, current);
    expect(PUT).toHaveBeenCalledWith("/api/criteria", { body: { ...criteria, locations: ["Lausanne", "GE"], min_rate: 100 } });
    expect(PUT).toHaveBeenCalledWith("/api/welcome", { body: { roles: ["DevOps"] } });
    expect(DELETE).toHaveBeenCalledTimes(1);
    expect(DELETE).toHaveBeenCalledWith("/api/alert-searches/{search_id}", { params: { path: { search_id: 2 } } });
    expect(POST).toHaveBeenCalledTimes(1);
    expect(POST).toHaveBeenCalledWith("/api/alert-searches", { body: { terms: "DevOps", location: "Genève" } });
    // Les sites où la recherche supprimée était déjà créée continuent d'écrire : le toast les nomme.
    expect(saved?.stillWriting.map((s) => s.name)).toEqual(["jobup", "LinkedIn"]);
  });

  it("enregistrer sans rien changer ne supprime ni ne crée aucune recherche", async () => {
    serve(["DevOps"], ["VD"]);
    const current = page([search(1, "DevOps", "Vaud")]);
    const loaded = await loadSearchCriteria(current);
    await saveSearchCriteria(loaded!, current);
    expect(DELETE).not.toHaveBeenCalled();
    expect(POST).not.toHaveBeenCalled();
  });

  it("un enregistrement refusé : null, aucune recherche touchée", async () => {
    serve(["DevOps"]);
    PUT.mockResolvedValue({ error: { detail: "non" } });
    expect(await saveSearchCriteria({ roles: [], places: [], rate: null }, page([search(1, "DevOps", null)]))).toBeNull();
    expect(DELETE).not.toHaveBeenCalled();
  });
});
