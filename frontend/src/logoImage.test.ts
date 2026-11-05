import { describe, expect, it } from "vitest";

import { isBlankLogo } from "./logoImage";

describe("isBlankLogo", () => {
  it("une image minuscule est vide", () => {
    const img = { naturalWidth: 1, naturalHeight: 1 } as HTMLImageElement;
    expect(isBlankLogo(img)).toBe(true);
  });
  it("sans canvas lisible (jsdom), une vraie image est gardée", () => {
    const img = { naturalWidth: 64, naturalHeight: 64 } as HTMLImageElement;
    expect(isBlankLogo(img)).toBe(false);
  });
});
