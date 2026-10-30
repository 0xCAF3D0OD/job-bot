/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";

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

  it("préparation, puis prêt avec sa taille, ou échec : l'état est sur le lien et annoncé", async () => {
    const link = document.createElement("a");
    link.textContent = "Word";
    link.setAttribute("href", "/api/letters/1/pdf");
    link.setAttribute("download", "");
    let resolve!: (r: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((r) => (resolve = r))));
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: () => "blob:x", revokeObjectURL: () => undefined }));
    const pending = download(link);
    expect(link.dataset.file).toBe("preparing");
    const status = () => document.querySelector("[data-test=file-status]");
    expect(status()?.getAttribute("role")).toBe("status");
    expect(status()?.textContent).toBe("Word : préparation…");
    resolve(new Response("x".repeat(86_000), { headers: { "content-disposition": 'attachment; filename="lettre.pdf"' } }));
    await pending;
    expect(link.dataset.file).toBe("done");
    expect(link.dataset.size).toBe("84 Ko");
    expect(status()?.textContent).toBe("Word téléchargé, 84 Ko.");

    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("", { status: 500 }))));
    await download(link);
    expect(link.dataset.file).toBe("failed");
    expect(status()?.textContent).toBe("Word : échec, réessaie.");
  });

  it("le bouton garde sa largeur : l'indicateur remplace l'icône, aucun texte ajouté pendant la préparation", () => {
    const css = readFileSync(resolvePath(__dirname, "../style.css"), "utf8");
    expect(css).toContain('a[download]:is([data-file="preparing"], [data-file="done"]) .with-icon > .icon:first-child { visibility: hidden; }');
    expect(css).not.toContain("Préparation…\"");
    expect(css).not.toMatch(/data-file="preparing"\][^{]*\{[^}]*color: var\(--muted\)/);
  });
});
