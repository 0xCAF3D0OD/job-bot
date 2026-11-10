/// <reference types="node" />
// Les textes de l'interface (MODIFICATIONS du 9 novembre, Textes) : apostrophe typographique, singulier pour 0 et 1,
// noms en français, numéros de téléphone espacés.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { cityOnly, companyPlace, frenchName, phoneDisplay, plural } from "./format";

const SRC = resolve(process.cwd(), "src");

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return files(path);
    return name.endsWith(".vue") ? [path] : [];
  });
}

describe("Textes (MODIFICATIONS du 9 novembre)", () => {
  it("le singulier pour 0 et 1, le pluriel dès 2", () => {
    expect(plural(0, "offre", "offres")).toBe("0 offre");
    expect(plural(1, "offre", "offres")).toBe("1 offre");
    expect(plural(2, "offre", "offres")).toBe("2 offres");
    expect(plural(0, "offre", "offres", "aucune offre")).toBe("aucune offre");
  });

  it("les noms des villes et des organisations en français, à l’affichage seulement", () => {
    expect(frenchName("ICRC · Geneva")).toBe("CICR · Genève");
    expect(frenchName("Bern, Switzerland")).toBe("Berne, Suisse");
    expect(frenchName("Zürich")).toBe("Zurich");
    expect(frenchName("Biel/Bienne")).toBe("Biel/Bienne");
    expect(frenchName(null)).toBeNull();
    expect(cityOnly("Basel, BS")).toBe("Bâle");
    expect(companyPlace("ICRC", "Geneva, GE")).toBe("CICR · Genève, GE");
    expect(companyPlace("ICRC", "Geneva, GE", true)).toBe("CICR · Genève");
    expect(companyPlace(null, "Luzern")).toBe("Lucerne");
  });

  it("un numéro de téléphone suisse s’affiche espacé ; les autres restent tels quels", () => {
    expect(phoneDisplay("+41764304321")).toBe("+41 76 430 43 21");
    expect(phoneDisplay("0041 76 430 43 21")).toBe("+41 76 430 43 21");
    expect(phoneDisplay("0764304321")).toBe("076 430 43 21");
    expect(phoneDisplay("076.430.43.21")).toBe("076 430 43 21");
    expect(phoneDisplay("+33 6 12 34 56 78")).toBe("+33 6 12 34 56 78");
  });

  it("plus d’apostrophe droite dans les textes des écrans", () => {
    const found: string[] = [];
    for (const path of files(SRC)) {
      const text = readFileSync(path, "utf8");
      const body = text.slice(text.indexOf("<template>"), text.lastIndexOf("</template>"));
      body.split("\n").forEach((line, i) => {
        if (/^\s*<!--/.test(line)) return;
        if (/[A-Za-zÀ-ÿ]'[A-Za-zÀ-ÿ]/.test(line.replace(/<!--.*?-->/g, ""))) found.push(`${relative(SRC, path)}:${i + 1}`);
      });
    }
    expect(found).toEqual([]);
  });
});
