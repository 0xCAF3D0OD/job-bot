import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { pageReady, pageTransition, startPage } from "./usePageTransition";

describe("transition des pages qui chargent (docs/61 §2)", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("rapide : rien ne s'affiche", () => {
    startPage("trainings");
    vi.advanceTimersByTime(100);
    pageReady("trainings");
    vi.advanceTimersByTime(500);
    expect(pageTransition.shown).toBe(false);
  });

  it("lent : le voile après 0,15 s, gardé 1,2 s au moins (docs/63 §3)", () => {
    startPage("trainings");
    vi.advanceTimersByTime(150);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    pageReady("trainings");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    expect(pageTransition.shown).toBe(false);
  });

  it("une page sans données : pas de transition", () => {
    startPage("diagnostic");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(false);
  });
});
