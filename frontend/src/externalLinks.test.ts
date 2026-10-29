import { describe, expect, it } from "vitest";

// Règle de Design : un lien qui ouvre un nouvel onglet le dit aux lecteurs d'écran, « (nouvel
// onglet) », dans son texte ou son aria-label (WCAG 3.2.5 ; MoreMenu fait de même).
const sources = import.meta.glob<string>(["./views/*.vue", "./components/**/*.vue"], {
  query: "?raw",
  import: "default",
  eager: true,
});

describe("liens vers un nouvel onglet", () => {
  it("chacun dit « (nouvel onglet) »", () => {
    const missing: string[] = [];
    let seen = 0;
    for (const [path, source] of Object.entries(sources)) {
      const template = source.slice(source.indexOf("<template>"));
      for (const match of template.matchAll(/<(a|RouterLink)\b([^>]*?\starget="_blank"[^>]*)>([\s\S]*?)<\/\1>/g)) {
        seen += 1;
        if (!/nouvel onglet/.test(match[2]! + match[3]!)) missing.push(`${path} : ${match[3]!.trim().slice(0, 40)}`);
      }
    }
    expect(seen).toBeGreaterThan(15);
    expect(missing).toEqual([]);
  });

  it("l'icône « ouvrir ailleurs » vient après le texte, partout (demande de Design)", () => {
    const before = Object.entries(sources)
      .filter(([, source]) => source.includes('<span class="with-icon"><AppIcon name="external" />'))
      .map(([path]) => path);
    expect(before).toEqual([]);
  });
});
