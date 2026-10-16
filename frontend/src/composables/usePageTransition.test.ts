import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { pageReady, pageTransition, startPage } from "./usePageTransition";

describe("transition des pages qui chargent (docs/61 §2)", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("rapide : rien ne s'affiche", () => {
    startPage("news");
    vi.advanceTimersByTime(100);
    pageReady("news");
    vi.advanceTimersByTime(500);
    expect(pageTransition.shown).toBe(false);
  });

  it("lent : le voile après 0,15 s, gardé 0,5 s au moins", () => {
    startPage("news");
    vi.advanceTimersByTime(150);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    pageReady("news");
    vi.advanceTimersByTime(300);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    expect(pageTransition.shown).toBe(false);
  });

  it("une page sans données : pas de transition", () => {
    startPage("profile");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(false);
  });
});
