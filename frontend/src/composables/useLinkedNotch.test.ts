import { describe, expect, it } from "vitest";

import { NOTCH_HALF, notchTop, PIN_GAP, PIN_HEIGHT, pinCenter, pinSide } from "./useLinkedNotch";

// Liaison carte → détail (§18 du 15 novembre) : le milieu de la pointe du rail tombe sur le centre de la flèche.
describe("useLinkedNotch, place de la pointe du rail", () => {
  it("top = centre de la flèche − haut de la zone − 30", () => {
    expect(notchTop(400, 150)).toBe(400 - 150 - NOTCH_HALF);
    for (const [center, zone] of [[312.4, 193], [655.75, 193], [880.2, 210.5]] as const) {
      const middle = zone + notchTop(center, zone) + NOTCH_HALF;
      expect(Math.abs(middle - center)).toBeLessThanOrEqual(1);
    }
  });

  it("la carte s'épingle en haut ou en bas quand son centre passe celui de la carte compacte", () => {
    const half = PIN_GAP + PIN_HEIGHT / 2;
    expect(pinSide(400, 200, 900)).toBeNull();
    expect(pinSide(200 + half, 200, 900)).toBeNull();
    expect(pinSide(200 + half - 1, 200, 900)).toBe("top");
    expect(pinSide(900 - half + 1, 200, 900)).toBe("bottom");
    expect(pinCenter("top", 200, 900)).toBe(200 + half);
    expect(pinCenter("bottom", 200, 900)).toBe(900 - half);
  });
});
