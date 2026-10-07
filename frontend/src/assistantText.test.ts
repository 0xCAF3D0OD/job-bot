import { describe, expect, it } from "vitest";

import { blocks, inline, readEvents } from "./assistantText";

describe("blocks", () => {
  it("découpe paragraphes, listes et blocs à copier", () => {
    const text = "Voici **trois** offres :\n\n- SRE\n- DevOps\n\n1. Relancer\n2. Préparer\n\n```\nBonjour,\nMerci.\n```\nFin";
    expect(blocks(text)).toEqual([
      { kind: "p", lines: [[{ text: "Voici ", bold: false }, { text: "trois", bold: true }, { text: " offres :", bold: false }]] },
      { kind: "list", ordered: false, items: [[{ text: "SRE", bold: false }], [{ text: "DevOps", bold: false }]] },
      { kind: "list", ordered: true, items: [[{ text: "Relancer", bold: false }], [{ text: "Préparer", bold: false }]] },
      { kind: "code", text: "Bonjour,\nMerci." },
      { kind: "p", lines: [[{ text: "Fin", bold: false }]] },
    ]);
  });

  it("garde un bloc à copier encore ouvert et un gras orphelin", () => {
    expect(blocks("```\nBonjour")).toEqual([{ kind: "code", text: "Bonjour" }]);
    expect(inline("en **cours")).toEqual([{ text: "en **cours", bold: false }]);
  });

  it("ne produit jamais de HTML", () => {
    expect(blocks("<img src=x onerror=alert(1)>")[0]).toEqual({
      kind: "p",
      lines: [[{ text: "<img src=x onerror=alert(1)>", bold: false }]],
    });
  });
});

describe("liens", () => {
  it("garde les chemins de la plateforme et les adresses https, sinon le texte", () => {
    expect(inline("Voir [l'offre](/candidatures/offres?offre=12) et [ce jour](/candidatures/suivi?mois=2026-10&jour=2026-10-02).")).toEqual([
      { text: "Voir ", bold: false },
      { text: "l'offre", bold: false, href: "/candidatures/offres?offre=12" },
      { text: " et ", bold: false },
      { text: "ce jour", bold: false, href: "/candidatures/suivi?mois=2026-10&jour=2026-10-02" },
      { text: ".", bold: false },
    ]);
    expect(inline("[cours](https://example.org/a)")).toEqual([
      { text: "cours", bold: false, href: "https://example.org/a", external: true },
    ]);
    expect(inline("[piège](javascript:alert(1))")[0]).toEqual({ text: "piège", bold: false });
    expect(inline("[ailleurs](/admin)")).toEqual([{ text: "ailleurs", bold: false }]);
    expect(inline("[préparer](/candidatures/offres/12/preparer)")[0]?.href).toBe("/candidatures/offres/12/preparer");
  });
});

describe("readEvents", () => {
  it("rend les événements complets et garde le reste", () => {
    const { events, rest } = readEvents('event: text\ndata: {"text":"Bon"}\n\nevent: text\ndata: {"te');
    expect(events).toEqual([{ event: "text", data: { text: "Bon" } }]);
    expect(rest).toBe('event: text\ndata: {"te');
  });
});
