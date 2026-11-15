import { describe, expect, it } from "vitest";

import { progressLabel } from "./trainingLabels";

describe("progressLabel", () => {
  it("écrit l'avancement comme la planche BilanOrdinateur", () => {
    expect(progressLabel({ modules_total: 12, modules_done: 6 })).toBe("Module 6 sur 12");
    expect(progressLabel({ progress: "module 6/12" })).toBe("Module 6 sur 12");
    expect(progressLabel({ progress: "Module 3 / 8" })).toBe("Module 3 sur 8");
    expect(progressLabel({ progress: "chapitre 2" })).toBe("chapitre 2");
    expect(progressLabel({ progress: null })).toBe("");
  });
});
