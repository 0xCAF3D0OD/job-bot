import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { ICONS } from "./icons";

// L'iconographie (docs/101) : plus de caractères utilisés comme icônes dans les gabarits, et le
// point pêche réservé à l'icône des actions IA.
const ROOT = join(__dirname);
function vueFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return vueFiles(path);
    return path.endsWith(".vue") ? [path] : [];
  });
}
function template(source: string): string {
  const start = source.indexOf("<template");
  const end = source.lastIndexOf("</template>");
  return start === -1 ? "" : source.slice(start, end);
}
// Les signes remplacés par une icône ; « › » reste permis comme séparateur dans une phrase
// (« Candidatures › Bilan »), pas seul dans un élément.
const GLYPHS = /[×←→↗＋↑↓⌄▶★✓✗]|👤|🧪|>\s*›\s*</u;

describe("L'iconographie (docs/101)", () => {
  it("aucun caractère ne sert d'icône dans les gabarits", () => {
    const offenders = vueFiles(ROOT).flatMap((file) =>
      template(readFileSync(file, "utf-8"))
        .split("\n")
        .map((line, index) => ({ line, index }))
        .filter(({ line }) => GLYPHS.test(line))
        .map(({ line, index }) => `${file.slice(ROOT.length + 1)}:${index + 1} ${line.trim()}`),
    );
    expect(offenders).toEqual([]);
  });

  it("le point pêche n'est que sur l'icône des actions IA", () => {
    const withDot = Object.entries(ICONS).filter(([, inner]) => inner.includes("icon-ai-dot"));
    expect(withDot.map(([name]) => name)).toEqual(["ai"]);
  });
});
