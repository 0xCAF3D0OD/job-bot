import { describe, expect, it } from "vitest";

import { fitChips } from "./chipFit";

const plus = () => 30;

describe("la rangée d'étiquettes sur une ligne (PR 46)", () => {
  it("tout tient : toutes les étiquettes, pas de pastille", () => {
    expect(fitChips([70, 60, 40], 182, 6, plus)).toBe(3);
    expect(fitChips([], 300, 6, plus)).toBe(0);
  });

  it("ça déborde : les dernières sont retirées, la place de « +k » est gardée", () => {
    // 70 + 6 + 60 + 6 + 40 + 6 + 80 = 268 > 200 ; avec « +2 » : 70 + 6 + 60 + 6 + 30 = 172.
    expect(fitChips([70, 60, 40, 80], 200, 6, plus)).toBe(2);
    // Une de moins quand la pastille ne tient plus.
    expect(fitChips([70, 60, 40, 80], 170, 6, plus)).toBe(1);
  });

  it("la première (« Gardée ») n'est jamais retirée, même trop à l'étroit", () => {
    expect(fitChips([70, 60, 40], 50, 6, plus)).toBe(1);
  });

  it("sans largeur mesurée, rien n'est retiré", () => {
    expect(fitChips([0, 0, 0], 0, 6, plus)).toBe(3);
  });
});
