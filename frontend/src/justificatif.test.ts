/// <reference types="node" />
// « justificatif » à la place de « preuve » partout (MODIFICATIONS du 8 novembre au soir, 16.4 et §11.2) :
// `grep -ri preuve frontend/src` ne doit plus rien trouver d'affiché. Restent permis : les commentaires, les noms
// internes (l'illustration « preuves-orp », l'ancienne adresse /candidatures/preuves) et le titre officiel du
// formulaire de l'ORP, que la feuille imprimée reprend mot pour mot.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = resolve(process.cwd(), "src");
const ALLOWED = [/"preuves-orp"/, /path: "preuves"/, /Preuves des recherches personnelles effectuées en vue de trouver un emploi/];

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return files(path);
    return /\.(vue|ts)$/.test(name) && !/\.test\.ts$|\.d\.ts$/.test(name) ? [path] : [];
  });
}

describe("Le mot « justificatif » (lot 16.4)", () => {
  it("aucun « preuve » affiché dans l'interface", () => {
    const found: string[] = [];
    for (const path of files(SRC)) {
      const text = readFileSync(path, "utf8").replace(/<!--[\s\S]*?-->/g, "").replace(/\/\*[\s\S]*?\*\//g, "");
      text.split("\n").forEach((line, index) => {
        const code = line.replace(/(^|\s)\/\/.*$/, "");
        if (/preuve/i.test(code) && !ALLOWED.some((ok) => ok.test(code))) found.push(`${relative(SRC, path)}:${index + 1} ${code.trim()}`);
      });
    }
    expect(found).toEqual([]);
  });
});
