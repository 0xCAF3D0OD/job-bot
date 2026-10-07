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

describe("readEvents", () => {
  it("rend les événements complets et garde le reste", () => {
    const { events, rest } = readEvents('event: text\ndata: {"text":"Bon"}\n\nevent: text\ndata: {"te');
    expect(events).toEqual([{ event: "text", data: { text: "Bon" } }]);
    expect(rest).toBe('event: text\ndata: {"te');
  });
});
