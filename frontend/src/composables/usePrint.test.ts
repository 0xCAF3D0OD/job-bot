import { afterEach, describe, expect, it, vi } from "vitest";

import { printSheet, zoomToFit } from "./usePrint";

afterEach(() => vi.restoreAllMocks());

describe("zoomToFit", () => {
  it("réduit un document qui dépasse à peine d'une page", () => {
    expect(zoomToFit(900, 1000)).toBe(1); // tient sur une page
    expect(zoomToFit(1050, 1000)).toBeCloseTo((1 / 1.05) * 0.97); // « Langues » seule en page 2
    expect(zoomToFit(1600, 1000)).toBe(1); // deuxième page bien remplie : on garde 2 pages
    expect(zoomToFit(2100, 1000)).toBeCloseTo((2 / 2.1) * 0.97);
    expect(zoomToFit(1300, 1000)).toBeGreaterThanOrEqual(0.8);
  });
});

describe("printSheet", () => {
  it("imprime une copie de la feuille seule, avec un titre de fichier, puis nettoie", () => {
    document.body.innerHTML = '<main><article class="cv-sheet print-sheet busy">CV</article></main>';
    const print = vi.spyOn(window, "print").mockImplementation(() => {});
    document.title = "job-bot";
    printSheet(document.querySelector<HTMLElement>(".cv-sheet")!, { title: "CV - Acme SA" });

    expect(print).toHaveBeenCalledOnce();
    const root = document.getElementById("print-root")!;
    expect(root.querySelector(".cv-sheet")?.classList.contains("busy")).toBe(false);
    expect(document.body.classList.contains("printing")).toBe(true);
    expect(document.title).toBe("CV - Acme SA");

    window.dispatchEvent(new Event("afterprint"));
    expect(document.getElementById("print-root")).toBeNull();
    expect(document.body.classList.contains("printing")).toBe(false);
    expect(document.title).toBe("job-bot");
  });
});
