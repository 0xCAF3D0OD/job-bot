import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// @ts-expect-error script node sans types
import { extract, glossary, glossaryMisses } from "../scripts/i18n-check.mjs";

// Les tests partent de frontend/ (npm run test).
const DOCS = join(process.cwd(), "..", "docs", "i18n");

describe("make i18n-check (docs/147 §5)", () => {
  it("lit les textes t() et la forme other de tn(), guillemets simples ou doubles", () => {
    const code = `t("Écarter l’offre"); :title="t('Bonjour {prenom}', { prenom })" tn(n, { one: "{n} offre", other: "{n} offres" })`;
    expect([...extract(code)]).toEqual(["Écarter l’offre", "Bonjour {prenom}", "{n} offres"]);
  });

  it("le glossaire allemand : ORP doit devenir RAV, les justificatifs des Belege", () => {
    const rows = glossary(readFileSync(join(DOCS, "glossaire-de.md"), "utf8"));
    expect(rows.find((r: { id: string }) => r.id === "office").target).toEqual(["RAV"]);
    const ids = (source: string, text: string) => glossaryMisses(rows, source, text).map((r: { id: string }) => r.id);
    expect(ids("Ton rendez-vous à l'ORP", "Dein Termin beim ORP")).toEqual(["office"]);
    expect(ids("Ton rendez-vous à l'ORP", "Dein Termin beim RAV")).toEqual([]);
    expect(ids("Remettre les justificatifs", "Belege einreichen")).toEqual([]);
    // Mot entier seulement : « corporate » ne contient pas le sigle ORP.
    expect(ids("Corporate", "Corporate")).toEqual([]);
  });

  it("chaque glossaire a les mêmes identifiants que le français", () => {
    const ids = (code: string) =>
      readFileSync(join(DOCS, `glossaire-${code}.md`), "utf8")
        .split("\n")
        .filter((l) => l.startsWith("| ") && !l.startsWith("| Id"))
        .map((l) => l.split("|")[1]!.trim());
    for (const code of ["de", "it", "en", "pt", "es", "sq"]) expect(ids(code)).toEqual(ids("fr"));
  });
});
