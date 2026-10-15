import { afterEach, describe, expect, it, vi } from "vitest";

import { download, fileName, fileSize } from "./useFileDownloads";

afterEach(() => vi.unstubAllGlobals());

describe("fichiers préparés (docs/59 §4)", () => {
  it("reprend le nom donné par le serveur, sinon la fin de l'adresse ; taille lisible", () => {
    expect(fileName("attachment; filename*=UTF-8''Lettre%20%C3%A9t%C3%A9.pdf", "/api/letters/1/pdf")).toBe("Lettre été.pdf");
    expect(fileName('attachment; filename="orp-2026-09.csv"', "/api/orp/2026-09/csv")).toBe("orp-2026-09.csv");
    expect(fileName(null, "/api/letters/1/docx")).toBe("docx");
    expect(fileSize(86_000)).toBe("84 Ko");
    expect(fileSize(2_500_000)).toBe("2,4 Mo");
  });

  it("le lien dit « Préparation… », puis « ✓ · taille », ou « Réessayer »", async () => {
    const link = document.createElement("a");
    link.setAttribute("href", "/api/letters/1/pdf");
    link.setAttribute("download", "");
    let resolve!: (r: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((r) => (resolve = r))));
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: () => "blob:x", revokeObjectURL: () => undefined }));
    const pending = download(link);
    expect(link.dataset.file).toBe("preparing");
    resolve(new Response("x".repeat(86_000), { headers: { "content-disposition": 'attachment; filename="lettre.pdf"' } }));
    await pending;
    expect(link.dataset.file).toBe("done");
    expect(link.dataset.size).toBe("84 Ko");

    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("", { status: 500 }))));
    await download(link);
    expect(link.dataset.file).toBe("failed");
  });
});
