import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { pageReady, pageTransition, resetFirstLoad, startPage } from "./usePageTransition";

describe("voile du premier chargement (planche « vide et chargement »)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetFirstLoad();
  });
  afterEach(() => vi.useRealTimers());

  it("rapide : rien ne s'affiche avant 300 ms", () => {
    startPage("trainings");
    vi.advanceTimersByTime(250);
    expect(pageTransition.shown).toBe(false);
    pageReady("trainings");
    vi.advanceTimersByTime(500);
    expect(pageTransition.shown).toBe(false);
  });

  it("lent : le voile après 300 ms, gardé 1,2 s au moins (docs/63 §3)", () => {
    startPage("trainings");
    vi.advanceTimersByTime(300);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    pageReady("trainings");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(200);
    expect(pageTransition.shown).toBe(false);
  });

  it("seulement au premier chargement : un changement de page n'a pas de voile", () => {
    startPage("today");
    pageReady("today");
    startPage("trainings");
    vi.advanceTimersByTime(2000);
    expect(pageTransition.shown).toBe(false);
  });

  it("une page sans données : pas de voile", () => {
    startPage("diagnostic");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(false);
  });
});
