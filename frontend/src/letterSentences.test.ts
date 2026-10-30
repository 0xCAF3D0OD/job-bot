import { describe, expect, it } from "vitest";

import { sentencesAt, sentenceSpans, withoutSentence } from "./letterSentences";

const TEXT = "J'ai construit alloremplacant.ch. Elle tourne en production à l'État de Vaud. J'aime Vue.";

describe("les phrases d'un paragraphe (« Pas vrai »)", () => {
  it("découpe comme le serveur", () => {
    expect(sentenceSpans(TEXT).map((s) => TEXT.slice(s.start, s.end))).toEqual([
      "J'ai construit alloremplacant.ch.",
      "Elle tourne en production à l'État de Vaud.",
      "J'aime Vue.",
    ]);
  });

  it("une sélection partielle devient la phrase entière ; le curseur seul, sa phrase", () => {
    const at = TEXT.indexOf("production");
    expect(sentencesAt(TEXT, at, at + 10)).toBe("Elle tourne en production à l'État de Vaud.");
    expect(sentencesAt(TEXT, at, at)).toBe("Elle tourne en production à l'État de Vaud.");
    // Une sélection à cheval sur deux phrases les prend toutes les deux.
    expect(sentencesAt(TEXT, 5, at)).toBe("J'ai construit alloremplacant.ch. Elle tourne en production à l'État de Vaud.");
  });

  it("retire la phrase et resserre les espaces", () => {
    expect(withoutSentence(TEXT, "Elle tourne en production à l'État de Vaud.")).toBe("J'ai construit alloremplacant.ch. J'aime Vue.");
  });
});
