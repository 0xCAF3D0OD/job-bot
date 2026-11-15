import { describe, expect, it } from "vitest";

import { arrowShown, LINE_WIDTH, NOTCH_MIDDLE, notchTop, VISIBLE_MARGIN } from "./useLinkedNotch";

// Liaison carte → détail (maquette du 15 novembre, §11) : le milieu de l'encoche tombe sur le centre de la flèche.
describe("useLinkedNotch, place de l'encoche", () => {
  it("top = centre de la flèche − haut de la zone − 21,3 − 1,5", () => {
    expect(notchTop(400, 150)).toBe(400 - 150 - NOTCH_MIDDLE - LINE_WIDTH);
    // Le milieu de l'encoche (top + trait + milieu du dessin) est à moins de 1 px du centre de la flèche.
    for (const [center, zone] of [[312.4, 193], [655.75, 193], [880.2, 210.5]] as const) {
      const middle = zone + notchTop(center, zone) + LINE_WIDTH + NOTCH_MIDDLE;
      expect(Math.abs(middle - center)).toBeLessThanOrEqual(1);
    }
  });

  it("flèche et encoche masquées hors de la partie visible de la liste (24 px de marge)", () => {
    expect(arrowShown(300, 200, 900)).toBe(true);
    expect(arrowShown(200 + VISIBLE_MARGIN, 200, 900)).toBe(true);
    expect(arrowShown(200 + VISIBLE_MARGIN - 1, 200, 900)).toBe(false);
    expect(arrowShown(900 - VISIBLE_MARGIN + 1, 200, 900)).toBe(false);
  });
});
