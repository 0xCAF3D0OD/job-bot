/// <reference types="node" />
// Contraste du texte (docs/28 §2) : chaque couleur de texte du thème atteint 4,5:1 sur les
// fonds où elle s'affiche, en mode clair et en mode sombre.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

// Lancé depuis frontend/ (npm test, vitest).
const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8");

// Une couleur s'écrit en hexadécimal ou renvoie à un rôle (« --accent: var(--primary-graphic) », docs/139 §3) :
// les renvois se résolvent après la fusion clair + sombre, comme dans le navigateur.
function declarations(block: string): Record<string, string> {
  const found: Record<string, string> = {};
  for (const match of block.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6}|var\(--[\w-]+\))\s*;/g)) found[match[1]!] = match[2]!;
  return found;
}

function resolved(raw: Record<string, string>): Record<string, string> {
  const value = (name: string, depth = 0): string | undefined => {
    const v = raw[name];
    const alias = v?.match(/^var\(--([\w-]+)\)$/);
    return alias && depth < 10 ? value(alias[1]!, depth + 1) : v;
  };
  return Object.fromEntries(Object.keys(raw).map((name) => [name, value(name)!]).filter(([, v]) => v?.startsWith("#")));
}

const lightRaw = declarations(css.slice(css.indexOf(":root {"), css.indexOf("}", css.indexOf(":root {"))));
const darkStart = css.indexOf("@media (prefers-color-scheme: dark)");
const light = resolved(lightRaw);
const dark = resolved({ ...lightRaw, ...declarations(css.slice(darkStart, css.indexOf("}\n}", darkStart))) });

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const f = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * f(r!) + 0.7152 * f(g!) + 0.0722 * f(b!);
}

function ratio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi! + 0.05) / (lo! + 0.05);
}

function mix(color: string, base: string, share: number): string {
  const channel = (hex: string, i: number) => parseInt(hex.slice(i, i + 2), 16);
  return `#${[1, 3, 5]
    .map((i) => Math.round(channel(color, i) * share + channel(base, i) * (1 - share)).toString(16).padStart(2, "0"))
    .join("")}`;
}

// Textes et fonds où ils s'affichent ; les fonds teintés sont ceux des pastilles.
const TEXTS = ["text", "muted", "accent", "ok-text", "orange-text", "down-text", "score-dig"];
const BACKGROUNDS = ["bg", "band", "surface", "panel"];

describe.each([
  ["clair", light],
  ["sombre", dark],
])("mode %s", (_mode, theme) => {
  it.each(TEXTS)("--%s lisible sur les fonds de page", (text) => {
    for (const background of BACKGROUNDS) {
      expect(ratio(theme[text]!, theme[background]!), `${text} sur ${background}`).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("--faint, réservé à ce qui n'est pas du texte (docs/135, 1.6.1)", () => {
  it("au moins 3,3:1 en clair et 3:1 en sombre sur les fonds de page", () => {
    for (const background of BACKGROUNDS) {
      expect(ratio(light.faint!, light[background]!), `clair, ${background}`).toBeGreaterThanOrEqual(3.3);
      expect(ratio(dark.faint!, dark[background]!), `sombre, ${background}`).toBeGreaterThanOrEqual(3);
    }
  });

  it("seulement pour les chevrons, les soulignés, l'encre des dessins, le bord des boutons secondaires, les jours vides, les cases ORP, les points des premiers pas à faire et le point « sans réponse » (1.6.20), la piste de l'interrupteur (1.6.23) ; le texte gris est en --muted", () => {
    const rules = [...css.matchAll(/([^{}]+)\{([^{}]*var\(--faint\)[^{}]*)\}/g)].map((m) => m[1]!.replace(/\/\*[\s\S]*?\*\//g, "").trim());
    for (const selector of rules) expect(selector).toMatch(/^(\.disclosure-chevron|\.hover-note|\.drawing |button:where\(|\.rhythm-dot|\.orp-month-bar|\.first-steps-dots|\.day-dots \.dot|:root input\[type="checkbox"\]|\.button-link)/);
    expect(rules.length).toBeGreaterThan(0);
  });
});

describe("pastilles teintées (mode clair)", () => {
  it("le texte reste lisible sur sa teinte", () => {
    const white = light.surface!;
    const pairs: [string, string][] = [
      [light.accent!, light["accent-soft"]!],
      [light.accent!, mix(light.accent!, white, 0.15)],
      [light["orange-text"]!, light["orange-soft"]!],
      [light["ok-text"]!, mix(light.ok!, white, 0.16)],
      ["#ffffff", light.accent!],
    ];
    for (const [text, background] of pairs) expect(ratio(text, background), `${text} sur ${background}`).toBeGreaterThanOrEqual(4.5);
  });
});

describe("étiquettes orange (docs/135)", () => {
  it("le texte orange reste lisible sur son fond, en clair et en sombre", () => {
    expect(ratio(light["orange-text"]!, light["orange-soft"]!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(dark["orange-text"]!, dark["orange-soft"]!)).toBeGreaterThanOrEqual(4.5);
  });
});

describe("la tuile du visage (1.6.16)", () => {
  it("le visage (--text) se voit sur chaque fond de tuile, en clair et en sombre", () => {
    for (const theme of [light, dark]) {
      for (const background of ["mint-soft", "accent-soft", "border", "orange-soft"]) {
        expect(ratio(theme.text!, theme[background]!), background).toBeGreaterThanOrEqual(3);
      }
    }
  });
});

describe("initiales des entreprises et pastille de la cloche (audit du 22.10.2026)", () => {
  it("l'initiale foncée sur les fonds clairs, le chiffre blanc sur un rouge assez sombre", () => {
    // Sur la menthe et le ciel, l'initiale reste foncée : --text en clair, --on-accent en sombre (1.6.15).
    for (const tone of ["mint", "sky"]) {
      expect(css).toMatch(new RegExp(`\\.logo\\.c\\d \\{ background: var\\(--${tone}\\); color: var\\(--text\\); \\}`));
      expect(ratio(light.text!, light[tone]!)).toBeGreaterThanOrEqual(4.5);
      expect(ratio(dark["on-accent"]!, dark[tone]!)).toBeGreaterThanOrEqual(4.5);
    }
    expect(css).toContain('@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .logo.c1, :root:not([data-theme="light"]) .logo.c2 { color: var(--on-accent); } }');
    expect(css).toContain(':root[data-theme="dark"] .logo.c1, :root[data-theme="dark"] .logo.c2 { color: var(--on-accent); }');
    // L'accent, avec --on-accent, en clair et en sombre ; jamais l'orange (docs/135, 1.6.3).
    expect(css).toContain(".logo.c0 { background: var(--primary); color: var(--on-accent); }");
    expect(ratio(light["on-accent"]!, light.primary!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(dark["on-accent"]!, dark.primary!)).toBeGreaterThanOrEqual(4.5);
    expect(css).not.toMatch(/\.logo\.c\d \{ background: var\(--orange\)/);
  });
});

describe("la pastille de la cloche et la sélection d'une offre (1.6.18)", () => {
  it("la cloche, seule pastille orange : 4,5:1 au moins en clair et en sombre", () => {
    // La pastille unique (CountBadge, 1.6.33), en orange pour la cloche : chiffre blanc sur l'orange foncé en clair,
    // chiffre de la couleur du fond sur l'orange clair du sombre chaud (docs/139).
    expect(css).toContain(".count-badge.orange { background: var(--orange); color: var(--on-primary); }");
    expect(css).toContain('@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .count-badge.orange { color: var(--bg); } }');
    expect(css).toContain(':root[data-theme="dark"] .count-badge.orange { color: var(--bg); }');
    expect(ratio(light["on-primary"]!, light.orange!)).toBeGreaterThanOrEqual(4.5);
    expect(ratio(dark.bg!, dark.orange!)).toBeGreaterThanOrEqual(4.5);
    expect(css).not.toContain("#c62a2f");
  });
  it("une offre sélectionnée : --muted reste à 4,5:1 sur le voile d'accent", () => {
    const share = Number(css.match(/\.offer-line\.selected \{ background: color-mix\(in srgb, var\(--accent\) (\d+)%/)![1]) / 100;
    for (const theme of [light, dark]) {
      expect(ratio(theme.muted!, mix(theme.accent!, theme.surface!, share))).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("les tuiles de Bilan (1.6.19)", () => {
  it("jamais de libellé coupé : la précision passe à la ligne", () => {
    const rule = (name: string) => css.match(new RegExp(`\\.${name} \\{[^}]*\\}`))![0];
    for (const name of ["dash-trend"]) {
      expect(rule(name)).not.toContain("ellipsis");
      expect(rule(name)).not.toContain("nowrap");
    }
    expect(rule("dash-tile-head")).toContain("flex-wrap: wrap");
  });
});

describe("le Suivi (1.6.20)", () => {
  it("un refus n'est pas une erreur : gris ; « sans réponse » en --faint, plus de couleur en dur", () => {
    expect(css).toContain(".app-status .dot.refus { background: var(--muted); }");
    expect(css).toContain(".app-status .dot.sans_reponse { background: var(--faint); }");
    expect(css).not.toContain("#c4c8d2");
  });

  it("le titre d'une ligne repliable en 600, ouverte ou fermée (comme Figma)", () => {
    expect(css).toMatch(/\.disclosure-title \{[^}]*font-weight: var\(--weight-semibold\)/);
  });
});

describe("les alertes (1.6.22)", () => {
  it("« Rien reçu depuis 24 heures » : le point en --orange, plus de couleur en dur", () => {
    // Depuis la pastille d'état (1.6.74), l'état « à faire » d'une alerte est une StatusPill au ton « todo ».
    expect(css).toContain(".state-pill.todo .state-pill-dot { background: var(--orange); }");
    // Une seule orange d'interface : --orange est l'alias de --warning (docs/139).
    expect(css).toContain("--orange: var(--warning);");
    expect(css).not.toContain("#e08a2e");
  });
});

describe("les champs (planche « Champs »)", () => {
  it("la bordure fait 3:1 au moins sur le champ et sur la carte, en clair et en sombre (WCAG 1.4.11)", () => {
    for (const theme of [light, dark]) {
      expect(ratio(theme["field-border"]!, theme["field-bg"]!)).toBeGreaterThanOrEqual(3);
      expect(ratio(theme["field-border"]!, theme.surface!)).toBeGreaterThanOrEqual(3);
      expect(ratio(theme.accent!, theme["field-bg"]!)).toBeGreaterThanOrEqual(3);
      expect(ratio(theme.text!, theme["field-bg"]!)).toBeGreaterThanOrEqual(4.5);
      expect(ratio(theme.muted!, theme["field-bg"]!)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("l'entrée affichée d'une liste groupée", () => {
  it("la phrase reste lisible sur le fond teinté, en clair et en sombre (WCAG 1.4.3)", () => {
    expect(css).toContain(".grouped-row-current .grouped-row-description { color: var(--text); }");
    for (const theme of [light, dark]) {
      expect(ratio(theme.text!, theme["accent-soft"]!)).toBeGreaterThanOrEqual(4.5);
      expect(ratio(theme.accent!, theme["accent-soft"]!)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe("radios (planche « Champs »)", () => {
  it("une radio est ronde : sa règle est au moins aussi forte que celle des cases, et vient après", () => {
    const common = css.indexOf(':root input:is([type="checkbox"]:not([role="switch"]), [type="radio"]) {');
    const round = css.indexOf(':root input[type="radio"]:not([role="switch"]) { border-radius: 50%; }');
    expect(common).toBeGreaterThan(0);
    expect(round).toBeGreaterThan(common);
  });
});

describe("l'interrupteur (1.6.23)", () => {
  it("la piste non cochée se voit sur la carte : --faint, 3:1 au moins (WCAG 1.4.11)", () => {
    expect(css).toMatch(/:root input\[type="checkbox"\]\[role="switch"\] \{[^}]*background: var\(--faint\)/);
    expect(ratio(light.faint!, light.surface!)).toBeGreaterThanOrEqual(3);
    expect(ratio(dark.faint!, dark.surface!)).toBeGreaterThanOrEqual(3);
  });
});

describe("les lignes repliables (1.6.24)", () => {
  it("le résumé n'est jamais coupé : il passe à la ligne", () => {
    const rule = css.match(/\.disclosure-value \{[^}]*\}/)![0];
    expect(rule).not.toContain("ellipsis");
    expect(rule).not.toContain("nowrap");
    // Jamais au milieu d'un mot : pas de largeur minimale nulle ni de coupure forcée.
    expect(rule).not.toContain("min-width: 0");
    expect(rule).not.toContain("break-word");
  });
});

describe("revue sur ordinateur (1.6.27)", () => {
  it("« en dessous » des semaines en gris ; le lien en bouton a le bord des boutons secondaires", () => {
    expect(css).toMatch(/\.button-link \{[^}]*border: 1px solid var\(--faint\)/);
  });
  it("le bouton « Assistant » laisse sa place en bas de la page", () => {
    expect(css).toMatch(/:root:has\(\.assistant-fab\) \.app-footer \{ padding-bottom: calc\(/);
  });
});

describe("l'anneau de la note : « Loin » et « À creuser » (revue de la PR 461)", () => {
  it("l'anneau de « Loin » se voit sur la carte (3:1, WCAG 1.4.11) et se distingue du gris chaud d'« À creuser »", () => {
    for (const theme of [light, dark]) {
      expect(ratio(theme["neutral-graphic"]!, theme.surface!)).toBeGreaterThanOrEqual(3);
      expect(ratio(theme["neutral-graphic"]!, theme["score-dig"]!)).toBeGreaterThanOrEqual(1.5);
      expect(ratio(theme["text-secondary"]!, theme.surface!)).toBeGreaterThanOrEqual(4.5);
    }
    expect(css).toContain(".score-ring.far { --ring: var(--neutral-graphic); --ring-text: var(--text-secondary); }");
    expect(css).toContain(".score-word.far .score-gauge { color: var(--neutral-graphic); }");
  });
});
