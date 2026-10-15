import { describe, expect, it } from "vitest";

import { fileName } from "./useFileDownloads";

describe("fileName (docs/58 §3.2)", () => {
  it("reprend le nom donné par le serveur, sinon la fin de l'adresse", () => {
    expect(fileName("attachment; filename*=UTF-8''Lettre%20%C3%A9t%C3%A9.pdf", "/api/letters/1/pdf")).toBe("Lettre été.pdf");
    expect(fileName('attachment; filename="orp-2026-09.csv"', "/api/orp/2026-09/csv")).toBe("orp-2026-09.csv");
    expect(fileName(null, "/api/letters/1/docx")).toBe("docx");
  });
});
