import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { pageReady, pageTransition, resetFirstLoad, startPage } from "./usePageTransition";

describe("voile du premier chargement (planche « vide et chargement »)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetFirstLoad();
  });
  afterEach(() => vi.useRealTimers());

  it("rapide : rien ne s’affiche avant 1 s (§15 du 9 novembre)", () => {
    startPage("trainings");
    vi.advanceTimersByTime(950);
    expect(pageTransition.shown).toBe(false);
    pageReady("trainings");
    vi.advanceTimersByTime(500);
    expect(pageTransition.shown).toBe(false);
  });

  it("lent : le voile après 1 s, gardé 1,2 s au moins (docs/63 §3)", () => {
    startPage("trainings");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(100);
    pageReady("trainings");
    vi.advanceTimersByTime(1000);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(200);
    expect(pageTransition.shown).toBe(false);
  });

  it("très lent : le voile s’efface après 10 s, la page montre ses blocs", () => {
    startPage("trainings");
    vi.advanceTimersByTime(9_900);
    expect(pageTransition.shown).toBe(true);
    vi.advanceTimersByTime(200);
    expect(pageTransition.shown).toBe(false);
  });

  it("seulement au premier chargement : un changement de page n’a pas de voile", () => {
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
